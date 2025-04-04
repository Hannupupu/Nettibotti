import os
import streamlit as st
from PyPDF2 import PdfReader
import re

# Kovakoodatut säännöt käyttötarpeille (Mbps)
SPEED_REQUIREMENTS = {
    "pelaaminen": 100,
    "4k": 50,
    "perhe": 200,
    "etätyö": 50,
    "peruskäyttö": 10
}

def parse_speeds_from_pdf(pdf_text):
    """Parsii PDF:stä pakettien nopeudet erittäin tarkasti"""
    packages = {}
    
    # Etsitään kaikki paketit ja niiden nopeudet
    # Tarkennettu regex joka vastaa PDF:n muotoilua
    speed_pattern = re.compile(
        r"(Kiinteä [SMXL\+]+|Yhteys Kotiin 5G [LXL\+XXL]+).*?"
        r"(?:Normaalinopeus[²2]|nopeus)[\s\|]*(\d+)\s*Mbit/s",
        re.DOTALL | re.IGNORECASE
    )
    
    # Lisäsääntöjä erikoistapauksille
    special_cases = {
        "Kiinteä S": 10,
        "Kiinteä M": 50,
        "Kiinteä L": 100,
        "Kiinteä XL": 200,
        "Kiinteä XL+": 300,
        "Kiinteä XXL": 600,
        "Yhteys Kotiin 5G L": 100,
        "Yhteys Kotiin 5G XL+": 300,
        "Yhteys Kotiin 5G XXL": 600
    }
    
    # 1. Etsitään ensin regexillä
    matches = speed_pattern.finditer(pdf_text)
    for match in matches:
        package = match.group(1).strip()
        speed = int(match.group(2))
        packages[package] = speed
    
    # 2. Täytetään puuttuvat erikoistapauksilla
    for package, speed in special_cases.items():
        if package not in packages:
            packages[package] = speed
    
    # 3. Manuaalinen tarkistus
    required_packages = [
        "Kiinteä S", "Kiinteä M", "Kiinteä L", 
        "Kiinteä XL", "Kiinteä XL+", "Kiinteä XXL",
        "Yhteys Kotiin 5G L", "Yhteys Kotiin 5G XL+", "Yhteys Kotiin 5G XXL"
    ]
    
    for package in required_packages:
        if package not in packages:
            st.warning(f"Pakettia {package} ei löytynyt PDF:stä!")
    
    return packages

def recommend_package(user_input, packages):
    """Suosittelee parasta pakettia käyttäjän tarpeiden mukaan"""
    user_input = user_input.lower()
    required_speed = 0
    
    # Päätetään vaadittu nopeus
    if "pelaaminen" in user_input:
        required_speed = max(required_speed, SPEED_REQUIREMENTS["pelaaminen"])
    if "4k" in user_input:
        required_speed = max(required_speed, SPEED_REQUIREMENTS["4k"])
    if "perhe" in user_input:
        required_speed = max(required_speed, SPEED_REQUIREMENTS["perhe"])
    if "etätyö" in user_input or "etätyöt" in user_input:
        required_speed = max(required_speed, SPEED_REQUIREMENTS["etätyö"])
    
    if required_speed == 0:  # Oletusarvo
        required_speed = SPEED_REQUIREMENTS["peruskäyttö"]
    
    # Etsitään halvin riittävä vaihtoehto
    suitable = []
    for name, speed in packages.items():
        if speed >= required_speed:
            suitable.append((name, speed))
    
    if not suitable:
        return None
    
    # Järjestetään nopeuden mukaan ja valitaan halvin
    suitable.sort(key=lambda x: x[1])
    return suitable[0]

def main():
    st.title("📶 Telian Nettiliittymäbotti")
    
    # Lataa ja jäsennä PDF
    pdf_path = "palvelukuvaus.pdf"
    if not os.path.exists(pdf_path):
        st.error("Virhe: palvelukuvaus.pdf -tiedostoa ei löydy!")
        st.stop()
    
    try:
        pdf_reader = PdfReader(pdf_path)
        pdf_text = "\n".join(page.extract_text() or "" for page in pdf_reader.pages)
        packages = parse_speeds_from_pdf(pdf_text)
        
        # Näytä ladatut tiedot debuggausta varten
        st.sidebar.subheader("PDF:stä löydetyt paketit")
        st.sidebar.write(packages)
        
    except Exception as e:
        st.error(f"Virhe PDF:n lukemisessa: {str(e)}")
        st.stop()
    
    # Käyttöliittymä
    user_input = st.text_area(
        "Kuvaile netin käyttötarkoituksiasi:",
        placeholder="Esim. 'Pelaaminen, 4K-videot, 3 hengen perhe'",
        height=150
    )
    
    if st.button("Hae tarkka suositus"):
        if not user_input.strip():
            st.warning("Kuvaile käyttötarkoituksia saadaksesi suosituksen")
            return
        
        recommendation = recommend_package(user_input, packages)
        
        if not recommendation:
            st.error("Sopivaa liittymäpakettia ei löytynyt")
            return
        
        name, speed = recommendation
        
        # Muodosta yksityiskohtainen perustelu
        reasons = []
        if "pelaaminen" in user_input.lower() and speed >= 100:
            reasons.append("riittää pelaamiseen (vaatii min. 100Mbps)")
        if "4k" in user_input.lower() and speed >= 50:
            reasons.append("riittää 4K-videoiden katseluun (min. 50Mbps)")
        if "perhe" in user_input.lower() and speed >= 200:
            reasons.append("riittää perhekäyttöön (min. 200Mbps)")
        
        if not reasons:
            reasons.append(f"sopii käyttötarkoitukseen (nopeus {speed}Mbps)")
        
        # Näytä tulos
        st.success(f"""
        **SUOSITUS:** {name}  
        **NOPEUS:** {speed} Mbps  
        **PERUSTELU:** {', '.join(reasons)}
        """)
        
        # Näytä vertailutaulukko
        st.subheader("Kaikki saatavilla olevat paketit")
        st.table({
            "Paketti": list(packages.keys()),
            "Nopeus (Mbps)": list(packages.values())
        })

if __name__ == "__main__":
    main()
