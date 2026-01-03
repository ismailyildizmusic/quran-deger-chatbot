from __future__ import annotations

import re
from dataclasses import dataclass

from rapidfuzz import fuzz

from src.api import search, ayah_multi
from src.values import VALUES, SEARCH_SEEDS, STOPWORDS_TR
from src.policy import detect_flags, build_prefix


@dataclass(frozen=True)
class Verse:
    ref: str           # "2:255"
    surah_no: int
    ayah_no: int
    surah_name_en: str
    surah_name_ar: str
    ar: str
    tr: str


def _tokenize(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r"[^a-zçğıöşü0-9\s]", " ", text)
    parts = [p.strip() for p in text.split() if p.strip()]
    parts = [p for p in parts if len(p) >= 3 and p not in STOPWORDS_TR]
    seen = set()
    out = []
    for p in parts:
        if p not in seen:
            out.append(p)
            seen.add(p)
    return out[:8]


def detect_values(user_text: str) -> list[str]:
    """
    Kullanıcı sorusundan en fazla 3 değer tespit eder.
    """
    t = user_text.lower()
    scored: list[tuple[str, int]] = []

    for val, kws in VALUES.items():
        score = 0
        for kw in kws:
            kw_l = kw.lower()
            if kw_l in t:
                score += 25
            else:
                score = max(score, fuzz.partial_ratio(kw_l, t))
        if score >= 60:
            scored.append((val, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [v for v, _ in scored][:3]


def _collect_candidates(user_text: str, values: list[str], edition_or_language: str) -> dict[str, dict]:
    """
    Search endpoint ile aday ayetleri toplar.
    Dönen: ref -> metadata(score vs.)
    """
    tokens = _tokenize(user_text)

    seeds = []
    for v in values:
        seeds.extend(SEARCH_SEEDS.get(v, []))

    query_terms = list(dict.fromkeys(tokens + seeds))[:12]
    candidates: dict[str, dict] = {}

    for q in query_terms:
        data = search(q, surah="all", edition_or_language=edition_or_language)
        for m in data.get("matches", [])[:30]:
            surah = m.get("surah", {}) or {}
            surah_no = int(surah.get("number", 0) or 0)
            surah_name_en = surah.get("englishName", "") or ""
            surah_name_ar = surah.get("name", "") or ""
            ayah_no = int(m.get("numberInSurah", 0) or 0)

            text_tr = (m.get("text") or "").strip()
            if not surah_no or not ayah_no:
                continue

            ref = f"{surah_no}:{ayah_no}"
            sim = fuzz.partial_ratio(text_tr.lower(), user_text.lower()) if text_tr else 0
            boost = 10 if q in seeds else 0
            score = sim + boost

            if ref not in candidates or score > candidates[ref]["score"]:
                candidates[ref] = {
                    "score": score,
                    "surah_no": surah_no,
                    "ayah_no": ayah_no,
                    "surah_name_en": surah_name_en,
                    "surah_name_ar": surah_name_ar,
                }

    return candidates


def fetch_best_verses(user_text: str, values: list[str], tr_edition_id: str, limit: int = 4) -> list[Verse]:
    """
    1) Search ile aday ref'leri bul
    2) En iyi limit tanesini seç
    3) Ayah multi ile Arapça + Türkçe meal getir
    """
    candidates = _collect_candidates(user_text, values, edition_or_language=tr_edition_id)
    best = sorted(candidates.items(), key=lambda x: x[1]["score"], reverse=True)[:limit]

    verses: list[Verse] = []
    editions = f"quran-uthmani,{tr_edition_id}"

    for ref, meta in best:
        items = ayah_multi(ref, editions)

        ar_item = next((x for x in items if x.get("edition", {}).get("identifier") == "quran-uthmani"), None)
        tr_item = next((x for x in items if x.get("edition", {}).get("identifier") == tr_edition_id), None)
        if not ar_item or not tr_item:
            continue

        surah_en = (ar_item.get("surah", {}) or {}).get("englishName", meta.get("surah_name_en", ""))
        surah_ar = (ar_item.get("surah", {}) or {}).get("name", meta.get("surah_name_ar", ""))

        verses.append(
            Verse(
                ref=ref,
                surah_no=meta["surah_no"],
                ayah_no=meta["ayah_no"],
                surah_name_en=surah_en,
                surah_name_ar=surah_ar,
                ar=(ar_item.get("text") or "").strip(),
                tr=(tr_item.get("text") or "").strip(),
            )
        )

    return verses


def compose_answer(user_text: str, values: list[str], verses: list[Verse]) -> str:
    """
    Sabit ve 'derin' format.
    Ayrıca 'haram/helal/yasak/doğru-yanlış' algılarsa uyarı ekler.
    """
    flags = detect_flags(user_text)
    prefix = build_prefix(flags)

    lines: list[str] = []
    if prefix:
        lines.append(prefix)

    lines.append("### 1) Değer analizi")
    if values:
        lines.append("- Bu soru şu değerlerle ilişkilidir: **" + ", ".join(values) + "**.")
    else:
        lines.append("- Sorunun değeri net değil; yine de genel ahlaki ilkeler üzerinden ele alıyorum.")

    if flags.get("risk_hits"):
        lines.append("\n### 1b) Soruda tespit edilen hassas ifadeler")
        for k, v in flags["risk_hits"].items():
            lines.append(f"- **{k}**: {', '.join(v)}")

    lines.append("\n### 2) Zarar / sonuç değerlendirmesi")
    lines.append("- **Hak boyutu:** Birinin hakkı zedeleniyor mu? (kul hakkı / adalet)")
    lines.append("- **Güven boyutu:** İlişkilerde güveni artırıyor mu, kırıyor mu?")
    lines.append("- **Mahremiyet boyutu:** Kişisel sınır ve rızaya saygı var mı?")
    lines.append("- **Uzun vade:** Bugün normalleşen davranış yarın karakter alışkanlığına dönüşür mü?")

    lines.append("\n### 3) Uygulanabilir adımlar (somut)")
    lines.append("1. **Zararı durdur:** Yanlışsa hemen devamını kes (paylaşma, yayma, haksız kazanç vb.).")
    lines.append("2. **Rıza / hak kontrolü:** Birinin rızası yoksa dur; hak varsa telafi et (özür + düzeltme + iade).")
    lines.append("3. **Doğrulama:** Bilgi ise kaynağı kontrol et; zan/iftiraya düşme.")
    lines.append("4.
