import os
import streamlit as st
from openai import OpenAI
from PyPDF2 import PdfReader

# API-avain
api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
if not api_key:
    st.error("API-avain puuttuu! Aseta se Settings > Secrets.")
    st.stop()

client = OpenAI(api_key=api_key)

# 🧠 PDF:n sisältö kontekstiksi
def load_pdf_context(file_path, max_chars=20000):
    reader = PdfReader(file_path)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    return text[:max_chars]

# 💬 Generoi vastaus GPT:llä
def generate_reply(user_input, context):
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": 
                 "Olet asiantunteva ja ystävällinen Telian asiakaspalvelija. "
                 "Käytä alla olevaa teknistä sisältöä apuna vastatessasi kysymyksiin nettiliittymistä. "
                 "Kerro suositus selkeästi, perustele konkreettisesti ja käytä arkikieltä."},
                {"role": "user", "content": f"Tässä on Telian palvelukuvaus:\n\n{context}"},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7,
            max_tokens=1200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Virhe vastauksen luonnissa: {str(e)}")
        return None

# 🖼️ Streamlit UI
def main():
    st.set_page_config(page_title="Telian Nettibotti", layout="wide")
    st.title("📶 Telian Nettibotti")

    if "context" not in st.session_state:
        with st.spinner("Ladataan PDF..."):
            try:
                context_text = load_pdf_context("palvelukuvaus.pdf")
                st.session_state.context = context_text
            except Exception as e:
                st.error(f"PDF:n lukeminen epäonnistui: {str(e)}")
                st.stop()

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hei! Miten voin auttaa nettiyhteyden valinnassa?"}
        ]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if user_input := st.chat_input("Kysy mitä tahansa nettiliittymistä..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.chat_message("user").write(user_input)

        with st.spinner("Haetaan paras vaihtoehto..."):
            reply = generate_reply(user_input, st.session_state.context)
            if reply:
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.chat_message("assistant").write(reply)

if __name__ == "__main__":
    main()
