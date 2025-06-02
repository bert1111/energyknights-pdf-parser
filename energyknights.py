import requests
import PyPDF2
from io import BytesIO
import re

@time_trigger("once(00:00)")  # Voer elke dag om 00:00 uit
def fetch_energy_prices():
    url = "https://www.energyknights.be/website/getCurrentTariffchart/variable/nl"
    response = requests.get(url)
    pdf_file = BytesIO(response.content)
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()

    # Debug: toon de volledige PDF-tekst (handig om de regex te testen)
    log.info("PDF tekst voor debugging:")
    log.info(text)

    # Zet tekst in één regel voor betere regex matching
    text = text.replace("\n", " ")

    # --- ENERGIE PRIJZEN ---
    match_dag = re.search(r"Verbruik dag.*?(\d+,\d+)", text)
    match_nacht = re.search(r"Verbruik nacht.*?(\d+,\d+)", text)
    match_solar = re.search(r"optie \"solar\".*?(\d+,\d+)", text)

    # --- NETTARIEF ---
    # Pas de regex aan aan de structuur van jouw PDF!
    match_net = re.search(r"Fluvius Limburg.*?(\d+,\d+)", text)
    if match_net:
        net_tarief = float(match_net.group(1).replace(",", ".")) / 100
    else:
        net_tarief = 0.0680  # valback waarde

    # --- BELASTINGEN EN HEFFINGEN ---
    # Pas de regex aan aan de structuur van jouw PDF!
    # Voorbeeld voor accijns, energiebijdrage, groene stroom, WKK
    match_accijns = re.search(r"Bijzondere accijns.*?(\d+,\d+)", text)
    accijns = float(match_accijns.group(1).replace(",", ".")) / 100 if match_accijns else 0.0503

    match_bijdrage = re.search(r"Energiebijdrage.*?(\d+,\d+)", text)
    bijdrage = float(match_bijdrage.group(1).replace(",", ".")) / 100 if match_bijdrage else 0.0020

    match_groen = re.search(r"Bijdrage groene stroom.*?(\d+,\d+)", text)
    groen = float(match_groen.group(1).replace(",", ".")) / 100 if match_groen else 0.0116

    match_wkk = re.search(r"Bijdrage WKK.*?(\d+,\d+)", text)
    wkk = float(match_wkk.group(1).replace(",", ".")) / 100 if match_wkk else 0.0036

    belastingen = accijns + bijdrage + groen + wkk

    # --- VASTE VERGOEDINGEN (indien in de PDF, anders handmatig) ---
    # Voorbeeld: match_databeheer = re.search(r"Databeheer.*?(\d+,\d+)", text)
    # Hier laten we het even achterwege, want dit is meestal een jaarlijkse kost en niet per kWh

    # --- BEREKENING VOOR DAGTARIEF ---
    if match_dag:
        prijs_dag = float(match_dag.group(1).replace(",", ".")) / 100
        totale_prijs_dag = prijs_dag + net_tarief + belastingen
        input_number.set_value(entity_id="input_number.aankoopprijs_elektriciteit_tarief_hoog", value=totale_prijs_dag)
        log.info(f"Totale dagtarief (hoog) gevonden: {totale_prijs_dag} EUR")

    # --- BEREKENING VOOR NACHTTARIEF ---
    if match_nacht:
        prijs_nacht = float(match_nacht.group(1).replace(",", ".")) / 100
        totale_prijs_nacht = prijs_nacht + net_tarief + belastingen
        input_number.set_value(entity_id="input_number.aankoopprijs_elektriciteit_tarief_laag", value=totale_prijs_nacht)
        log.info(f"Totale nachttarief (laag) gevonden: {totale_prijs_nacht} EUR")

    # --- BEREKENING VOOR SOLAR (TERUGLEVERING) ---
    if match_solar:
        prijs_solar = float(match_solar.group(1).replace(",", ".")) / 100
        # Voor teruglevering gelden meestal geen netbeheerkosten of belastingen
        input_number.set_value(entity_id="input_number.verkoopprijs_elektriciteit_zonnepanelen", value=prijs_solar)
        log.info(f"Solar (teruglevering) gevonden: {prijs_solar} EUR")

input("Druk op Enter om het venster te sluiten...")
