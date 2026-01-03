from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from rapidfuzz import fuzz

from src.api import search, ayah_multi
from src.values import VALUES, SEARCH_SEEDS, STOPWORDS_TR


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
    # benzersizleştir, sırayı koru
    seen = set()
    out = []
    for p in parts:
        if p not in seen:
            out.append(p)
            seen.add(p)
    return out[:8]


def detect_values(user_text: str) -> list[str]:
    """
    Basit ama etkili: anahtar kelime + fuzzy.
    En fazla 3 değer döndürür.
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


def _collect_candidates(
    user_text: str,
    values: list[str],
    edition_or_language: str,
) -> dict[str, dict]:
    """
    Aday ayetleri arama endpoint'inden toplar.
    Dönen: ref -> { score, surah_no, ayah_no, snippet_tr, surah_name_en, surah_name_ar }
    """
    tokens = _tokenize(user_text)

    # arama kelimeleri: kullanıcının kelimeleri + değer seed'leri
    seeds = []
    for v in values:
        seeds.extend(SEARCH_SEEDS.get(v, []))
    query_terms = list(dict.fromkeys(tokens + seeds))[:12]

    candidates: dict[str, dict] = {}

    for q in query_terms:
        data = search(q, surah="all", edition_or_language=edition_or_language)
        for m in data.get("matches", [])[:30]:
            # Match yapısı API'ye göre değişebilir; güvenli okuyalım
            surah = m.get("surah", {}) or {}
            surah_no = int(surah.get("number", 0) or 0)
            surah_name_en = surah.get("englishName", "") or ""
            surah_name_ar = surah.get("name", "") or ""
            ayah_no = int(m.get("numberInSurah", 0) or 0)

            text_tr = (m.get("text") or "").strip()
            if not surah_no or not ayah_no:
                continue

            ref = f"{surah_no}:{ayah_no}"
            # alaka skoru: ayet metni ile soru benzerliği
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
                    "snippet_tr": text_tr,
                }

    return candidates


def fetch_best_verses(
    user_text: str,
    values: list[str],
    tr_edition_id: str,
    limit: int = 4,
) -> list[Verse]:
    """
    1) search ile aday ref'ler
    2) en iyilerini seç
    3) /ayah/{ref}/editions/arabic,tr ile tam metin çek
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
    Yüzeyselliği kıran sabit format:
    1) Değer analizi
    2) Zarar/sonuç
    3) Uygulanabilir adımlar
    4) Kur’an referansları (sûre:ayet + Arapça + Türkçe)
    """
    lines: list[str] = []

    lines.append("### 1) Değer analizi")
    if values:
        lines.append("- Bu soru şu değerlerle ilişkilidir: **" + ", ".join(values) + "**.")
    else:
        lines.append("- Sorunun değeri net değil; yine de genel ahlaki ilkeler üzerinden ele alıyorum.")

    lines.append("\n### 2) Zarar / sonuç değerlendirmesi")
    lines.append("- **Hak boyutu:** Birinin hakkı zedeleniyor mu? (kul hakkı / adalet)")
    lines.append("- **Güven boyutu:** İlişkilerde güveni artırıyor mu, kırıyor mu?")
    lines.append("- **Mahremiyet boyutu:** Kişisel sınır ve rızaya saygı var mı?")
    lines.append("- **Uzun vade:** Bugün normalleşen davranış yarın karakter alışkanlığına dönüşür mü?")

    lines.append("\n### 3) Uygulanabilir adımlar (somut)")
    lines.append("1. **Zararı durdur:** Yanlışsa hemen devamını kes (paylaşma, yayma, haksız kazanç vb.).")
    lines.append("2. **Rıza / hak kontrolü:** Birinin rızası yoksa dur; hak varsa telafi et (özür + düzeltme + iade).")
    lines.append("3. **Doğrulama:** Bilgi ise kaynağı kontrol et; zan/iftiraya düşme.")
    lines.append("4. **Alternatif üret:** Aynı hedefe hak ihlalsiz ulaşmanın yolunu seç.")
    lines.append("5. **Tekrarı önle:** Kendin için net bir kural koy (mahremiyet, emek, israf vb.).")

    lines.append("\n### 4) Kur’an referansları (sûre:ayet)")
    if not verses:
        lines.append("- Bu soru için aramada yeterince güçlü eşleşme bulamadım. (Anahtar kelimeleri genişletmek gerekir.)")
    else:
        for v in verses:
            lines.append(f"- **{v.surah_name_en} / {v.surah_name_ar} ({v.ref})**")
            lines.append(f"  - Arapça: {v.ar}")
            lines.append(f"  - Türkçe: {v.tr}")

    lines.append("\n> Not: Bu uygulama kişiye özel dini hüküm/fetva vermez; **değer temelli** rehberlik sağlar.")
    return "\n".join(lines)
