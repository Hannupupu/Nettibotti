import os
import streamlit as st
from openai import OpenAI
from PyPDF2 import PdfReader
import re

# Alusta OpenAI
api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
if not api_key:
    st.error("API-avain puuttuu! Aseta se Settings > Secrets.")
    st.stop()

client = OpenAI(api_key=api_key)

def extract_package_info(pdf_path):
    """Poimii pakettien tiedot PDF:stä"""
    try:
        reader = PdfReader(pdf_path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        
        # Poimi paketit ja nopeudet
        packages = {}
        matches = re.finditer(
            r"(Kiinteä [A-Z+]+|Yhteys Kotiin 5G [A-Z+]+).*?(\d+)\s*Mbit/s", 
            text, re.DOTALL
        )
        for match in matches:
            packages[match.group(1)] = int(match.group(2))
            
        return {
            "packages": packages,
            "tech_info": text[:20000]  # Otetaan 20k merkkiä analyysiin
        }
    except Exception as e:
        st.error(f"Virhe PDF:n lukemisessa: {str(e)}")
        return None

def generate_response(user_input, context):
    """Luo käyttäjäystävällisen vastauksen"""
    prompt = f"""
    Olet Telian asiakaspalveluedustaja. Vastaa käyttäjän kysymykseen käyttämällä alla olevia tietoja.

    TELIAN PAKETIT JA NOPEUDET:
    {context['packages']}

    TEKNISET TIEDOT:
    {context['tech_info']}

    KÄYTTÄJÄN KYSYMYS:
    {user_input}

    VASTAUSOHJEET:
    1. Keskitty käyttäjän tarpeisiin
    2. Älä mainitse dokumentteja tai teknisia lähdeviittauksia
    3. Anna selkeät suositukset konkreettisin perustein
    4. Käytä arkikieltä ja välttää teknisia termejä
    5. Jos et tiedä vastausta, sano rehellisesti
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Virhe API-kutsussa: {str(e)}")
        return None

def main():
    st.title("📶 Telian Nettineuvoja")
    
    # Lataa tiedot
    pdf_info = extract_package_info("palvelukuvaus.pdf")
    if not pdf_info:
        st.error("Palvelutietoja ei saatavilla")
        st.stop()
    
    # Keskusteluhistoria
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Miten voin auttaa nettiä valitessa?"}
        ]
    
    # Näytä historia
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])
    
    # Käsittele syöte
    if user_input := st.chat_input("Kirjoita kysymyksesi..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.chat_message("user").write(user_input)
        
        with st.spinner("Etsin parasta ratkaisua..."):
            response = generate_response(user_input, pdf_info)
            if response:
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )
                st.chat_message("assistant").write(response)

if __name__ == "__main__":
    main()
