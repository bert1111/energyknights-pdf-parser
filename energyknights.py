def fetch_energy_prices():
    import re

    def download_and_extract(url):
        import requests
        import PyPDF2
        from io import BytesIO

        response = requests.get(url)
        pdf_file = BytesIO(response.content)
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text

    url = "https://www.energyknights.be/website/getCurrentTariffchart/variable/nl"
    # Gebruik task.executor om blokkeren te voorkomen!
    text = task.executor(download_and_extract, url)
    log.info("PDF tekst voor debugging:")
    log.info(text)

    text = text.replace("\n", " ")

    # --- ENERGIEPRIJZEN ---
    match_dag = re.search(r"Verbruik dag.*?(\d+,\d+)", text)
    match_nacht = re.search(r"Verbruik nacht.*?(\d+,\d+)", text)
    match_solar = re.search(r"optie\s*\"solar\".*?(\d+,\d+)", text)

    # --- NETTARIEF (voorbeeld voor digitale meter, Fluvius Limburg) ---
    match_net = re.search(r"Fluvius \(Limburg\)\s*(\d+,\d+)", text)
    net_tarief = float(match_net.group(1).replace(",", ".")) / 100 if match_net else 0.0680

    # --- BELASTINGEN EN HEFFINGEN ---
    match_accijns = re.search(r"Bijzondere accijns.*?(\d+,\d+)", text)
    accijns = float(match_accijns.group(1).replace(",", ".")) / 100 if match_accijns else 0.050329

    match_bijdrage = re.search(r"Energiebijdrage.*?(\d+,\d+)", text)
    bijdrage = float(match_bijdrage.group(1).replace(",", ".")) / 100 if match_bijdrage else 0.002042

    match_groen = re.search(r"Bijdrage groene stroom.*?(\d+,\d+)", text)
    groen = float(match_groen.group(1).replace(",", ".")) / 100 if match_groen else 0.0116

    match_wkk = re.search(r"Bijdrage WKK.*?(\d+,\d+)", text)
    wkk = float(match_wkk.group(1).replace(",", ".")) / 100 if match_wkk else 0.0036

    belastingen = accijns + bijdrage + groen + wkk

    # --- BEREKENING VOOR DAGTARIEF ---
    if match_dag:
        prijs_dag = float(match_dag.group(1).replace(",", ".")) / 100
        totale_prijs_dag = prijs_dag + net_tarief + belastingen
        input_number.set_value(entity_id="input_number.aankoopprijs_elektriciteit_tarief_hoog", value=totale_prijs_dag)
        log.info(f"Totale dagtarief (hoog) gevonden: {totale_prijs_dag} EUR")
    else:
        log.warning("Dagtarief niet gevonden!")

    # --- BEREKENING VOOR NACHTTARIEF ---
    if match_nacht:
        prijs_nacht = float(match_nacht.group(1).replace(",", ".")) / 100
        totale_prijs_nacht = prijs_nacht + net_tarief + belastingen
        input_number.set_value(entity_id="input_number.aankoopprijs_elektriciteit_tarief_laag", value=totale_prijs_nacht)
        log.info(f"Totale nachttarief (laag) gevonden: {totale_prijs_nacht} EUR")
    else:
        log.warning("Nachttarief niet gevonden!")

    # --- BEREKENING VOOR SOLAR (TERUGLEVERING) ---
    if match_solar:
        prijs_solar = float(match_solar.group(1).replace(",", ".")) / 100
        input_number.set_value(entity_id="input_number.verkoopprijs_elektriciteit_zonnepanelen", value=prijs_solar)
        log.info(f"Solar (teruglevering) gevonden: {prijs_solar} EUR")
    else:
        log.warning("Solar (teruglevering) niet gevonden!")
