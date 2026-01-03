import streamlit as st

from src.policy import detect_flags
from src.api import list_tr_translations
from src.logic import detect_values, fetch_best_verses, compose_answer

# -----------------------------
# SAYFA AYARLARI
# -----------------------------
st.set_page_config(page_title="Doğru Karar Atölyesi", layout="wide")
st.title("🧠 Doğru Karar Atölyesi — Kur’an Referanslı Değerler Chatbotu")
st.caption("Adalet • Kul hakkı • Doğruluk • Mahremiyet • Güven • Emek • İsraf")

with st.expander("⚠️ Kullanım Notu", expanded=True):
    st.write(
        "Bu uygulama kişiye özel dini hüküm/fetva üretmez. "
        "Kur’an’dan **ayetleri API üzerinden aynen** getirir ve değer temelli rehberlik yapar."
    )

# -----------------------------
# DATA: Türkçe mealler
# -----------------------------
@st.cache_data(ttl=24 * 3600)
def _load_tr_editions():
    return list_tr_translations()

editions = _load_tr_editions()

label_to_id = {}
labels = []
for e in editions:
    label = f"{e.get('englishName','(Unknown)')} — {e.get('identifier','')}"
    labels.append(label)
    label_to_id[label] = e.get("identifier")

selected_label = st.selectbox("Türkçe meal seç (API edition)", labels)
tr_edition_id = label_to_id[selected_label]

# -----------------------------
# DEĞER MODU
# -----------------------------
mode = st.radio(
    "Değer tespiti modu",
    ["Otomatik (sorudan yakala)", "Ben seçeceğim"],
    horizontal=True
)

manual_values = []
if mode == "Ben seçeceğim":
    manual_values = st.multiselect(
        "Değer(ler) seç",
        ["Adalet", "Kul hakkı", "Doğruluk", "Mahremiyet", "Güven", "Emek", "İsraf"],
        default=["Doğruluk"]
    )

st.divider()

# -----------------------------
# LAYOUT: 2 sütun
# -----------------------------
left, right = st.columns([2, 1], gap="large")

# -----------------------------
# SESSION STATE (tek yerde)
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sağ panelde göstereceğimiz "son analiz" verileri
if "last_analysis" not in st.session_state:
    st.session_state.last_analysis = None  # dict veya None

# -----------------------------
# SOL: CHAT
# -----------------------------
with left:
    # geçmişi göster
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_text = st.chat_input("Sorunu yaz (örn: 'İzinsiz fotoğraf paylaşmak doğru mu?')")

    if user_text:
        # kullanıcı mesajı
        st.session_state.messages.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.markdown(user_text)

        # hesaplamalar
        with st.chat_message("assistant"):
            with st.spinner("Kur’an metninde arıyorum ve cevap taslağını hazırlıyorum..."):
                values = manual_values if manual_values else detect_values(user_text)
                flags = detect_flags(user_text)

                verses = fetch_best_verses(
                    user_text=user_text,
                    values=values,
                    tr_edition_id=tr_edition_id,
                    limit=4
                )
                answer = compose_answer(
                    user_text=user_text,
                    values=values,
                    verses=verses
                )

            st.markdown(answer)

        # asistan mesajını kaydet
        st.session_state.messages.append({"role": "assistant", "content": answer})

        # sağ panel için "son analiz"i kaydet
        st.session_state.last_analysis = {
            "values": values,
            "flags": flags,
            "verses": verses,
        }

# -----------------------------
# SAĞ: ANALİZ PANELİ
# -----------------------------
with right:
    st.subheader("🔎 Analiz Paneli")
    st.caption("Son soruya göre otomatik çıkarımlar")

    analysis = st.session_state.last_analysis

    if not analysis:
        st.info("Bir soru yazınca burada değerler, hassas ifadeler ve ayet referansları görünecek.")
    else:
        values = analysis["values"]
        flags = analysis["flags"]
        verses = analysis["verses"]

        st.markdown("**Tespit edilen değerler:**")
        st.write(values if values else ["(Belirsiz)"])

        if flags.get("fetva_request"):
            st.warning("Fetva/hüküm talebi algılandı → rehberlik moduna geçildi.")
        elif flags.get("right_wrong_request"):
            st.info("Doğru/yanlış talebi algılandı → hak/zarar analizi uygulanacak.")

        if flags.get("risk_hits"):
            st.markdown("**Hassas / riskli ifadeler:**")
            for k, v in flags["risk_hits"].items():
                st.write(f"- {k}: {', '.join(v)}")
        else:
            st.markdown("**Hassas / riskli ifadeler:**")
            st.write(["(Yok)"])

        st.markdown("**Getirilen ayet referansları:**")
        if verses:
            for vv in verses:
                st.write(f"- {vv.ref} — {vv.surah_name_en}")
        else:
            st.write(["(Ayet bulunamadı)"])
