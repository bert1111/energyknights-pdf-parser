import requests
import PyPDF2
from io import BytesIO
import re
from datetime import datetime

@service
async def fetch_energyknights_prices():
    """
    Downloadt de laatste tariefkaart van Energy Knights, controleert de datum,
    leest de prijzen uit en zet ze in Home Assistant input_numbers.
    """
    url = "https://www.energyknights.be/website/getCurrentTariffchart/variable/nl"
    log.info(f"Downloaden van: {url}")
    
    # Download PDF via task.executor (blocking call)
    response = await task.executor(requests.get, url)
    if response.status_code != 200:
        log.error(f"Kon PDF niet downloaden, status code: {response.status_code}")
        return
    
    # Lees PDF in via task.executor (ook blocking)
    pdf_file = BytesIO(response.content)
    reader = await task.executor(PyPDF2.PdfReader, pdf_file)
    
    # Tekst uit alle pagina's halen
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text.replace("\n", " ")
    
    # Debug: log de eerste 500 tekens
    log.info(f"Eerste 500 tekens uit PDF: {text[:500]}")
    
    # --- DATUM VALIDATIE ---
    # Zoek naar de datum in het formaat "2025-07" in de tariefkaart
    current_date = datetime.now()
    current_month_str = current_date.strftime("%Y-%m")
    
    # Zoek naar datum patronen in de PDF tekst
    date_patterns = [
        r"(\d{4}-\d{2})",  # Format: 2025-07
        r"Tariefkaart\s*(\d{4}-\d{2})",  # Format: "Tariefkaart 2025-07"
        r"(\d{4}-\d{2})\s*tot",  # Format: "2025-07 tot"
    ]
    
    tariff_month = None
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            tariff_month = match.group(1)
            break
    
    if tariff_month:
        log.info(f"Gevonden tariefmaand in PDF: {tariff_month}")
        log.info(f"Huidige maand: {current_month_str}")
        
        if tariff_month != current_month_str:
            log.warning(f"Tariefkaart is niet voor de huidige maand ({current_month_str}). Gevonden: {tariff_month}")
            log.warning("Script wordt niet verder uitgevoerd.")
            return
        else:
            log.info("✅ Tariefkaart is voor de huidige maand, doorgaan met verwerking")
    else:
        log.warning("Geen datum gevonden in tariefkaart, doorgaan met verwerking")
    
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
        await service.call("input_number", "set_value", 
                          entity_id="input_number.aankoopprijs_elektriciteit_tarief_hoog", 
                          value=round(totale_prijs_dag, 4))
        log.info(f"Totale dagtarief (hoog) gevonden: {totale_prijs_dag} EUR/kWh")
    else:
        log.warning("Dagtarief niet gevonden!")
    
    # --- BEREKENING VOOR NACHTTARIEF ---
    if match_nacht:
        prijs_nacht = float(match_nacht.group(1).replace(",", ".")) / 100
        totale_prijs_nacht = prijs_nacht + net_tarief + belastingen
        await service.call("input_number", "set_value", 
                          entity_id="input_number.aankoopprijs_elektriciteit_tarief_laag", 
                          value=round(totale_prijs_nacht, 4))
        log.info(f"Totale nachttarief (laag) gevonden: {totale_prijs_nacht} EUR/kWh")
    else:
        log.warning("Nachttarief niet gevonden!")
    
    # --- BEREKENING VOOR SOLAR (TERUGLEVERING) ---
    if match_solar:
        prijs_solar = float(match_solar.group(1).replace(",", ".")) / 100
        await service.call("input_number", "set_value", 
                          entity_id="input_number.verkoopprijs_elektriciteit_zonnepanelen", 
                          value=round(prijs_solar, 4))
        log.info(f"Solar (teruglevering) gevonden: {prijs_solar} EUR/kWh")
    else:
        log.warning("Solar (teruglevering) niet gevonden!")
    
    log.info("Energieprijzen van Energy Knights zijn bijgewerkt.")