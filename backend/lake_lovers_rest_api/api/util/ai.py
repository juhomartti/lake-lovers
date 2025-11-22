from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import requests

def ai_summary(data):

    try:
        response = requests.get("https://rajapinnat.ymparisto.fi/api/kansalaishavainnot/1.0/requests.json?service_code=algaebloom_service_code_201808151546171&extension=true")
    except Exception as e:
        print(e)
        response = ""

    

    try:
# client etsii API-avaimen automaattisesti ympäristömuuttujasta (GEMINI_API_KEY)
        load_dotenv()
        client = genai.Client(api_key=os.getenv("API_KEY"))
    except Exception:
        print("\nVIRHE: Gemini API-avainta ei löytynyt. Aseta GEMINI_API_KEY (esim. VS Code .env-tiedostoon).")
        exit()

    # 1. PROMPT ENGINEERING (Rajauspromptit)
    # NYT ON VIELÄ VIIKOITTAINEN
    system_prompt = (
        "Olet Suomen Ympäristökeskuksen (SYKE) asiantuntija. Tehtäväsi on laatia "
        "viikoittainen sinilevätiedote 20 viimeisimmän päivän havaintojen perusteella. "
        "Tiedotteen tulee olla analyyttinen, yleistajuinen ja noudattaa Suomen vesistöjen "
        "virallista tiedotustyyliä. Vastaa AINOASTAAN suomeksi. Vastaa yhtenäisenä, useamman "
        "kappaleen raporttina, maksimissaan 400 sanaa."
    )

    user_prompt = f"""
    Analysoi alla oleva sinilevähavaintoja koskeva data ja laadi siitä tiivis, viikoittaista 
    sinilevätiedotetta vastaava yhteenveto. Muodosta tiedote seuraavien ohjeiden mukaisesti:

    1. Yleistilanne: Aloita kuvaamalla lyhyesti, kuinka monessa havainnossa havaittiin levää yleisesti (LevätilanneTxt != "Ei levää") ja kuinka monessa havaittiin runsas/erittäin runsas esiintymä.
    2. Alueellinen katsaus: Nimeä ja kuvaile lyhyesti ne ELY-keskusten alueet (2-3 keskeisintä), joissa havaittiin eniten runsaita tai erittäin runsaita leväesiintymiä. Anna alueellinen yhteenveto, älä luettele yksittäisiä paikkoja.
    3. Loppuhuomio: Sisällytä lyhyt yhteenveto.
    4. Ohjeistus: Päätä tiedote lyhyeen ja ytimekkääseen ohjeistukseen toimenpiteistä sinilevän havaitsemisen varalle.

    DATA ALKAA TÄSTÄ:
    {data}
    DATA PÄÄTTYY TÄHÄN.
    """

    # Mallin asetukset
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=0.4, 
    )

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config=config,
        )
        print(response.text)
        return response.text

    except Exception as e:
        print(f"VIRHE Geminin kutsussa: {e}")
        return e