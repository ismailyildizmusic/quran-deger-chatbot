
import re

FETVA_TRIGGERS = [
    "haram mı", "helal mi", "günah mı", "caiz mi", "fetva", "hükmü",
    "farz mı", "vacip mi", "mekruh mu"
]

RIGHT_WRONG_TRIGGERS = [
    "doğru mu", "yanlış mı", "yasak mı", "suç mu", "doğru değil mi", "yanlış değil mi",
    "haram", "helal", "günah", "caiz"
]

RISK_TOPICS = {
    "mahremiyet": ["izinsiz", "ifşa", "fotoğraf", "video", "dm", "özel", "gizli"],
    "yalan_iftira": ["yalan", "iftira", "dedikodu", "gıybet", "zan"],
    "haksiz_kazanc": ["çalmak", "kopya", "intihal", "çalıntı", "dolandır"],
    "siddet": ["döv", "vur", "bıçak", "silah", "intikam"]
}

def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()

def detect_flags(user_text: str) -> dict:
    t = _norm(user_text)

    fetva = any(x in t for x in FETVA_TRIGGERS)
    right_wrong = any(x in t for x in RIGHT_WRONG_TRIGGERS)

    hits = {}
    for topic, kws in RISK_TOPICS.items():
        found = [kw for kw in kws if kw in t]
        if found:
            hits[topic] = found

    return {
        "fetva_request": fetva,
        "right_wrong_request": right_wrong,
        "risk_hits": hits
    }

def build_prefix(flags: dict) -> str:
    if flags.get("fetva_request"):
        return (
            "⚠️ **Not:** Bu uygulama kişiye özel dini hüküm/fetva vermez. "
            "Kur’an’ın genel ilkeleri ve değerler üzerinden rehberlik sağlar.\n\n"
        )
    if flags.get("right_wrong_request"):
        return (
            "ℹ️ Sorunda **doğru/yanlış** talebi algılandı. "
            "Cevap, **hak/zarar analizi + değerler** üzerinden verilecektir.\n\n"
        )
    return ""
