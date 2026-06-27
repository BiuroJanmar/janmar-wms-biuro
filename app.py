import streamlit as st
import requests
import json
from datetime import datetime
from io import BytesIO

# Importy do awaryjnego generowania PDF w biurze (z polskimi znakami)
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# URL DO TEGO SAMEGO FOLDERU W FIREBASE
FIREBASE_URL = "https://janmar-kalkulator-default-rtdb.europe-west1.firebasedatabase.app/janmar_wms_rampa.json"

st.set_page_config(page_title="Janmar WMS - Biuro & Handel", page_icon="🏢", layout="wide")

# --- ZABEZPIECZENIE HASŁEM ---
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

# --- POBIERANIE DANYCH Z FIREBASE ---
@st.cache_data(ttl=5)  # Odświeżanie danych co 5 sekund
def pobierz_dane_firebase():
    try:
        response = requests.get(FIREBASE_URL)
        if response.status_code == 200 and response.json():
            return response.json()
    except:
        pass
    return {}

baza_danych = pobierz_dane_firebase()

# REJESTRACJA CZCIONKI DO PDF
def generuj_pdf_lokalny(d):
    try:
        pdfmetrics.registerFont(TTFont('PolishFont', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
        pdfmetrics.registerFont(TTFont('PolishFont-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
        f_regular = 'PolishFont'
        f_bold = 'PolishFont-Bold'
    except:
        f_regular = 'Helvetica'
        f_bold = 'Helvetica-Bold'

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottom=30)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', fontName=f_bold, fontSize=18, leading=22, textColor=colors.HexColor('#1F497D'), alignment=1)
    sub_style = ParagraphStyle('SubStyle', fontName=f_regular, fontSize=10, leading=14)
    header_table_style = ParagraphStyle('HeaderTableStyle', fontName=f_bold, fontSize=9, leading=11, textColor=colors.white, alignment=1)
    cell_table_style = ParagraphStyle('CellTableStyle', fontName=f_regular, fontSize=9, leading=11, alignment=0)
    cell_table_center = ParagraphStyle('CellTableCenter', fontName=f_regular, fontSize=9, leading=11, alignment=1)
    
    story.append(Paragraph(f"DOKUMENT PZ - PRZYJĘCIE ZEWNĘTRZNE nr: {d['nr_pz']}", title_style))
    story.append(Spacer(1, 15))
    
    status_kolor = '#2ecc71' if d['status_jakosci'] == 'ZIELONY' else ('#f39c12' if d['status_jakosci'] == 'POMARAŃCZOWY' else '#e74c3c')
    
    dane_ogolne = [
        [Paragraph(f"<b>Nabywca / Magazyn:</b><br/>GPW JANMAR SP. Z O.O.<br/>ul. Gołaśka 3/58, Kraków", sub_style),
         Paragraph(f"<b>Dostawca:</b><br/>{d['dostawca_nazwa']}<br/>ID: {d['dostawca_id']}<br/>Tel: {d['dostawca_tel']}", sub_style)],
        [Paragraph(f"<b>Data dostawy:</b> {d['data']}<br/><b>Sporządził:</b> {d['magazynier']}", sub_style),
         Paragraph(f"<font color='{status_kolor}'><b>STATUS JAKOŚCI: {d['status_jakosci']}</b></font><br/>Uwagi: {d['uwagi']}", sub_style)]
    ]
    t_ogolne = Table(dane_ogolne, colWidths=[270, 270])
    t_ogolne.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F2F5F8')), ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#1F497D')), ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D9D9D9')), ('TOPPADDING', (0,0), (-1,-1), 8), ('BOTTOMPADDING', (0,0), (-1,-1), 8)]))
    story.append(t_ogolne)
    story.append(Spacer(1, 20))
    
    tabela_towarowa = [
        [Paragraph("Parametr rozliczeniowy", header_table_style), Paragraph("Dostarczono (Wjazd)", header_table_style), Paragraph("Pobrano (Wyjazd)", header_table_style), Paragraph("Saldo Końcowe", header_table_style)],
        [Paragraph(f"Towar: {d['towar']}", cell_table_style), Paragraph(f"{d['netto']} kg/szt.", cell_table_center), Paragraph("-", cell_table_center), Paragraph(f"{d['netto']} kg/szt.", cell_table_center)],
        [Paragraph(f"Opakowania ({d['opakowanie_typ']})", cell_table_style), Paragraph(f"{d['opakowania_przywiezione']} szt.", cell_table_center), Paragraph(f"{d['opakowania_pobrane']} szt.", cell_table_center), Paragraph(f"{d['opakowania_przywiezione'] - d['opakowania_pobrane']} szt.", cell_table_center)],
        [Paragraph(f"Palety ({d['palety_typ']})", cell_table_style), Paragraph(f"{d['palety_przywiezione']} szt.", cell_table_center), Paragraph(f"{d['palety_pobrane']} szt.", cell_table_center), Paragraph(f"{d['palety_przywiezione'] - d['palety_pobrane']} szt.", cell_table_center)]
    ]
    t_towarowa = Table(tabela_towarowa, colWidths=[250, 100, 95, 95])
    t_towarowa.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1F497D')), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#1F497D')), ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D9D9D9')), ('TOPPADDING', (0,0), (-1,-1), 8), ('BOTTOMPADDING', (0,0), (-1,-1), 8)]))
    story.append(t_towarowa)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# --- OBSŁUGA LINKU QR DLA HANDLOWCA (Parametr w adresie URL) ---
query_params = st.query_params
if "p" in query_params:
    skanowany_id = query_params["p"]
    st.title("📱 SZYBKI PODGLĄD PALETY DLA HANDLOWCA")
    st.write("---")
    
    if skanowany_id in baza_danych:
        d = baza_danych[skanowany_id]
        st.success(f"✅ Znaleziono dostawę: {d['nr_pz']}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📦 TOWAR", d["towar"])
            st.metric("⚖️ WAGA NETTO", f"{d['netto']} kg")
        with col2:
            st.metric("👤 DOSTAWCA", d["dostawca_nazwa"])
            st.metric("📅 DATA WPISU", d["data"])
            
        status_colors = {"ZIELONY": "green", "POMARAŃCZOWY": "orange", "CZERWONY": "red"}
        st.markdown(f"### 🛡️ Status Jakości: :{status_colors.get(d['status_jakosci'], 'blue')}[{d['status_jakosci']}]")
        st.info(f"**Uwagi/Powód:** {d['uwagi']}")
        
        st.markdown("### 🔄 Saldo Opakowań z tej dostawy:")
        st.write(f"* **Skrzynki ({d['opakowanie_typ']}):** Przywieziono: `{d['opakowania_przywiezione']}` | Zabrano: `{d['opakowania_pobrane']}` | Saldo: `{d['opakowania_przywiezione'] - d['opakowania_pobrane']}`")
        st.write(f"* **Palety ({d['palety_typ']}):** Przywieziono: `{d['palety_przywiezione']}` | Zabrano: `{d['palety_pobrane']}` | Saldo: `{d['palety_przywiezione'] - d['palety_pobrane']}`")
        
        pdf_h = generuj_pdf_lokalny(d)
        st.download_button("📥 POBIERZ PEŁNY RAPORT PDF NA TELEFON", data=pdf_h, file_name=f"{skanowany_id}.pdf")
    else:
        st.error("❌ Nie znaleziono takiego numeru dostawy w bazie. Upewnij się, że rampa zatwierdziła dokument.")
    st.stop()


# --- WIDOK DLA BIURA (KOMPUTER FAKTURZYSTKI) ---
st.title("🏢 JANMAR WMS - PANEL SYSTEMOWY BIURA")
st.write("---")

if not baza_danych:
    st.warning("📭 Baza danych jest obecnie pusta. Brak zarejestrowanych przyjęć na rampie.")
    st.stop()

# Wyciągamy unikalną listę dostawców
lista_kontrahentow = {}
for k, v in baza_danych.items():
    lista_kontrahentow[v["dostawca_id"]] = v["dostawca_nazwa"]

st.sidebar.header("🗂️ Wybór Kontrahenta")
wybrany_dostawca_id = st.sidebar.selectbox(
    "Wybierz dostawcę z listy, aby zobaczyć historię:",
    options=list(lista_kontrahentow.keys()),
    format_func=lambda x: f"{lista_kontrahentow[x]} ({x})"
)

if wybrany_dostawca_id:
    st.header(f"📊 Historia i Salda: {lista_kontrahentow[wybrany_dostawca_id]}")
    st.write(f"ID Dostawcy: `{wybrany_dostawca_id}`")
    
    # Filtrujemy wjazdy tylko tego jednego dostawcy
    wjazdy_klienta = [v for k, v in baza_danych.items() if v["dostawca_id"] == wybrany_dostawca_id]
    
    # Obliczanie globalnego salda opakowań
    total_przywiezione_op = sum(w["opakowania_przywiezione"] for w in wjazdy_klienta)
    total_pobrane_op = sum(w["opakowania_pobrane"] for w in wjazdy_klienta)
    total_saldo_op = total_przywiezione_op - total_pobrane_op
    
    total_przywiezione_pal = sum(w["palety_przywiezione"] for w in wjazdy_klienta)
    total_pobrane_pal = sum(w["palety_pobrane"] for w in wjazdy_klienta)
    total_saldo_pal = total_przywiezione_pal - total_pobrane_pal
    
    # Podsumowanie kafli (Salda)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("📦 Łączna ilość wjazdów", len(wjazdy_klienta))
    with c2: st.metric("⚖️ Całkowity tonaż (kg)", f"{sum(w['netto'] for w in wjazdy_klienta):,.1f}")
    with c3: st.metric("📥 Saldo Skrzynek (W magazynie)", f"{total_saldo_op} szt.", help=f"Przywieziono: {total_przywiezione_op} | Pobrał: {total_pobrane_op}")
    with c4: st.metric("🪵 Saldo Palet (W magazynie)", f"{total_saldo_pal} szt.", help=f"Przywieziono: {total_przywiezione_pal} | Pobrał: {total_pobrane_pal}")
    
    st.write("---")
    st.subheader("📝 Lista wszystkich dostaw pancernego segregatora:")
    
    # Wyświetlanie historii dostaw w czytelnych wierszach
    for w in sorted(wjazdy_klienta, key=lambda x: x['data'], reverse=True):
        with st.expander(f"📅 {w['data']} — {w['nr_pz']} — {w['towar']} ({w['netto']} kg)"):
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.markdown(f"**📦 Szczegóły towaru:**")
                st.write(f"* **Asortyment:** {w['towar']}")
                st.write(f"* **Waga netto:** {w['netto']} kg")
                st.write(f"* **Magazynier przyjmujący:** {w['magazynier']}")
            with col_b:
                st.markdown(f"**🔄 Rozliczenie opakowań:**")
                st.write(f"* **Skrzynki:** Przywiezione: `{w['opakowania_przywiezione']}` | Pobrane: `{w['opakowania_pobrane']}` (Saldo: `{w['opakowania_przywiezione'] - w['opakowania_pobrane']}`)")
                st.write(f"* **Palety:** Przywiezione: `{w['palety_przywiezione']}` | Pobrane: `{w['palety_pobrane']}` (Saldo: `{w['palety_przywiezione'] - w['palety_pobrane']}`)")
                st.write(f"* **Typ palet:** {w['palety_typ']}")
            with col_c:
                st.markdown(f"**🛡️ Ocena jakościowa:**")
                st.write(f"* **Status:** {w['status_jakosci']}")
                st.write(f"* **Uwagi:** {w['uwagi']}")
                
                # Przycisk do wygenerowania i pobrania PDF
                pdf_biuro = generuj_pdf_lokalny(w)
                st.download_button(
                    label=f"📥 POBIERZ PDF DLA {w['nr_pz'].replace('/','_')}",
                    data=pdf_biuro,
                    file_name=f"{w['nr_pz'].replace('/','_')}.pdf",
                    mime="application/pdf",
                    key=w['nr_pz']
                )
