import os
import tiktoken
import streamlit as st
from openai import OpenAI
from PyPDF2 import PdfReader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS

# Alusta Streamlit-sivun asetukset
st.set_page_config(
    page_title="Telian Nettiliittymäbotti",
    page_icon="📶",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Alusta OpenAI-asiakas
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_vectorstore(pdf_path):
    """Lataa PDF-tiedosto ja luo vektorivaraston"""
    if not os.path.exists(pdf_path):
        st.warning("PDF-tiedostoa ei löydy!")
        return None
        
    pdf_reader = PdfReader(pdf_path)
    text = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
    
    text_splitter = CharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    
    return FAISS.from_texts(chunks, OpenAIEmbeddings())

def get_token_count(text):
    """Laskee tokenien määrän"""
    return len(tiktoken.get_encoding("cl100k_base").encode(text))

def adjust_max_tokens(prompt, max_total=4097, max_response=1000):
    """Säätää tokenien maksimimäärää"""
    return min(max_total - get_token_count(prompt), max_response)

def main():
    st.title("📶 Telian Nettiliittymäbotti")
    st.markdown("""
    <style>
    .main {background-color: #f5f5f5; padding: 2rem;}
    .stTextArea textarea {min-height: 150px;}
    </style>
    """, unsafe_allow_html=True)

    st.info("Kerro netin käyttötarpeistasi, ja suosittelemme sopivimman Telian liittymäpaketin!")

    # Alusta sovellus
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Kysy käyttäjältä tietoja
    with st.form("netti_form"):
        user_input = st.text_area(
            "Kuvaile netin käyttötarkoituksiasi (esim. pelaaminen, etätyöt, perhekäyttö):",
            placeholder="Esimerkiksi: 'Tarvitsen netin pelailuun ja 4K-videoiden katseluun...'"
        )
        
        submitted = st.form_submit_button("Hae suositus")
        if submitted and user_input:
            with st.spinner("Etsitään parasta liittymäpakettia..."):
                try:
                    # Muodosta prompt
                    prompt = f"""
                    Asiakkaan kuvaus: {user_input}

                    Valitse yksi seuraavista Telian liittymäpaketeista:
                    - Kiinteä S/M/L/XL/XL+/XXL
                    - Yhteys Kotiin 5G L/XL+/XXL

                    Perustelut:
                    1. Pelaaminen: vähintään 100Mbps
                    2. 4K-videot: vähintään 50Mbps
                    3. Perhekäyttö: vähintään 200Mbps
                    4. Etätyöt: vähintään 50Mbps + pieni latency

                    Muotoile vastaus:
                    SUOSITUS: [Paketin nimi]
                    NOPEUS: [Mbps]
                    PERUSTELU: [Lyhyt selitys]
                    """

                    # Lähetä pyyntö OpenAI:lle
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7,
                        max_tokens=adjust_max_tokens(prompt)
                    )

                    # Näytä tulos
                    st.success("### Liittymäsuositus")
                    st.markdown(response.choices[0].message.content)
                    
                except Exception as e:
                    st.error(f"Virhe suositusta haettaessa: {str(e)}")

if __name__ == "__main__":
    main()