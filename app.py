import streamlit as st

from src.api import list_tr_translations
from src.logic import detect_values, fetch_best_verses, compose_answer

st.set_page_config(page_title="Doğru Karar Atölyesi", layout="wide")
st.title("🧠 Doğru Karar Atölyesi — Kur’an Referanslı Değerler Chatbotu")

st.caption("Adalet • Kul hakkı • Doğruluk • Mahremiyet • Güven • Emek • İsraf")

with st.expander("⚠️ Kullanım Notu", expanded=True):
    st.write(
        "Bu uygulama kişiye özel dini hüküm/fetva üretmez. "
        "Kur’an’dan **ayetleri API üzerinden aynen** getirir ve değer temelli rehberlik yapar."
    )

@st.cache_data(ttl=24 * 3600)
def _load_tr_editions():
    return list_tr_translations()

editions = _load_tr_editions()

# Dropdown label oluştur
label_to_id = {}
labels = []
for e in editions:
    # e örnek alanlar: englishName, name, identifier
    label = f"{e.get('englishName','(Unknown)')} — {e.get('identifier','')}"
    labels.append(label)
    label_to_id[label] = e.get("identifier")

selected_label = st.selectbox("Türkçe meal seç (API edition)", labels)
tr_edition_id = label_to_id[selected_label]

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

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_text = st.chat_input("Sorunu yaz (örn: 'İzinsiz fotoğraf paylaşmak doğru mu?')")

if user_text:
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    with st.chat_message("assistant"):
        with st.spinner("Kur’an metninde arıyorum ve cevap taslağını hazırlıyorum..."):
            values = manual_values if manual_values else detect_values(user_text)
            verses = fetch_best_verses(user_text=user_text, values=values, tr_edition_id=tr_edition_id, limit=4)
            answer = compose_answer(user_text=user_text, values=values, verses=verses)

        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
