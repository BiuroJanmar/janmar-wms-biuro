import streamlit as st
import requests

FIREBASE_URL = "https://janmar-kalkulator-default-rtdb.europe-west1.firebasedatabase.app/janmar_wms_rampa.json"

st.set_page_config(page_title="Janmar WMS - Biuro & Handel", page_icon="🏢", layout="wide")

if "autoryzowany_biuro" not in st.session_state:
    st.session_state["autoryzowany_biuro"] = False

if not st.session_state["autoryzowany_biuro"]:
    st.title("🏢 JANMAR WMS - PANEL BIUROWY")
    st.write("---")
    haslo_input = st.text_input("Wprowadź hasło dostępowe:", type="password")
    if st.button("🔓 ZALOGUJ"):
        if haslo_input == "Janmar2026":
            st.session_state["autoryzowany_biuro"] = True
            st.rerun()
        else:
            st.error("❌ Błędne hasło!")
    st.stop()

@st.cache_data(ttl=2)
def pobierz_dane_firebase():
    try:
        response = requests.get(FIREBASE_URL)
        if response.status_code == 200 and response.json():
            return response.json()
    except:
        pass
    return {}

baza_danych = pobierz_dane_firebase()

# --- OBSŁUGA LINKU QR DLA HANDLOWCA ---
query_params = st.query_params
if "p" in query_params:
    skanowany_id = query_params["p"]
    st.title("📱 SZYBKI PODGLĄD PALETY DLA HANDLOWCA")
    if skanowany_id in baza_danych:
        d = baza_danych[skanowany_id]
        st.success(f"✅ Znaleziono dostawę: {d['nr_pz']}")
        st.metric("📦 TOWAR", d["towar"])
        st.metric("⚖️ WAGA NETTO", f"{d['netto']} kg")
        if "link_drive" in d:
            st.link_button("📥 OTWÓRZ RAPORT PDF Z PODPISEM", d["link_drive"])
    else:
        st.error("❌ Brak rekordu.")
    st.stop()

# --- WIDOK DLA BIURA (KOMPUTER FAKTURZYSTKI) ---
st.title("🏢 JANMAR WMS - PANEL SYSTEMOWY BIURA")
st.write("---")

if not baza_danych:
    st.warning("📭 Baza danych jest pusta.")
    st.stop()

lista_kontrahentow = {}
for k, v in baza_danych.items():
    lista_kontrahentow[v["dostawca_id"]] = v["dostawca_nazwa"]

st.sidebar.header("🗂️ Wybór Kontrahenta")
wybrany_dostawca_id = st.sidebar.selectbox("Wybierz dostawcę:", options=list(lista_kontrahentow.keys()), format_func=lambda x: f"{lista_kontrahentow[x]} ({x})")

if wybrany_dostawca_id:
    st.header(f"📊 Historia i Salda: {lista_kontrahentow[wybrany_dostawca_id]}")
    wjazdy_klienta = [v for k, v in baza_danych.items() if v["dostawca_id"] == wybrany_dostawca_id]
    
    total_przywiezione_op = sum(w["opakowania_przywiezione"] for w in wjazdy_klienta)
    total_pobrane_op = sum(w["opakowania_pobrane"] for w in wjazdy_klienta)
    
    c1, c2 = st.columns(2)
    with c1: st.metric("📦 Łączna ilość wjazdów", len(wjazdy_klienta))
    with c2: st.metric("⚖️ Całkowity tonaż (kg)", f"{sum(w['netto'] for w in wjazdy_klienta):,.1f}")
    
    st.write("---")
    for w in sorted(wjazdy_klienta, key=lambda x: x['data'], reverse=True):
        with st.expander(f"📅 {w['data']} — {w['nr_pz']} — {w['towar']}"):
            if "link_drive" in w:
                st.link_button(
                    label=f"🔵 OTWÓRZ ORYGINALNY RAPORT Z PODPISEM (DRIVE)",
                    url=w["link_drive"]
                )
            else:
                st.warning("⚠️ Ten starszy wpis nie posiada pliku na Google Drive.")
