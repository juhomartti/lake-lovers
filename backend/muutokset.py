import pandas as pd
import re
import os
from datetime import timedelta, date
from google import genai
from google.genai import types

# ************************************************
# ASETUKSET
# ************************************************

# Aseta TÄYDELLINEN polku sinun result.csv tiedostoosi
file_path = "C:\\Users\\35845\\Documents\\PYTHON\\Hackhaton\\result.csv" 

# ************************************************
# APUFUNKTIO DMS -> DD
# ************************************************

def dms_to_dd(dms_str):
    """
    Muuntaa koordinaattimerkkijonon (DMS) desimaaliasteiksi (DD).
    """
    if not isinstance(dms_str, str):
        return None
    
    match = re.search(r'(\d+)\D+(\d+)\D+([\d\.]+)\D+([NnSsEeWw])', dms_str)
    
    if match:
        degrees = float(match.group(1))
        minutes = float(match.group(2))
        seconds = float(match.group(3))
        direction = match.group(4).upper()

        decimal_degrees = degrees + minutes / 60 + seconds / 3600

        if direction in ('S', 'W'):
            decimal_degrees *= -1
            
        return decimal_degrees
    return None

# ************************************************
# VAIHE 1: DATAN LUKU JA PUHDISTUS
# ************************************************

# 1. Tiedoston lukeminen
try:
    df = pd.read_csv(file_path, sep=';', encoding='utf-8')
except UnicodeDecodeError:
    df = pd.read_csv(file_path, sep=';', encoding='iso-8859-1')
except FileNotFoundError:
    print(f"VIRHE: Tiedostoa ei löytynyt polusta: {file_path}")
    exit()

# 2. Koordinaattien muunnos (DMS -> DD)
df['Koordinaatit_Clean'] = df['Koordinaatit'].str.replace('"', '').str.strip()
df[['Leveysaste_DMS', 'Pituusaste_DMS']] = df['Koordinaatit_Clean'].str.split(',', expand=True)

df['Latitude_DD'] = df['Leveysaste_DMS'].apply(dms_to_dd)
df['Longitude_DD'] = df['Pituusaste_DMS'].apply(dms_to_dd)

# 3. Päivämäärän muunnos
df['Päivämäärä'] = pd.to_datetime(df['Päivämäärä'], errors='coerce')

# 4. Turhien/Puuttuvien sarakkeiden/rivien poisto
df = df.drop(columns=['Koordinaatit', 'Koordinaatit_Clean', 'Leveysaste_DMS', 'Pituusaste_DMS'])
# Poistetaan rivit, joissa ei ole päivämäärää tai koordinaatteja
df = df.dropna(subset=['Päivämäärä', 'Latitude_DD', 'Longitude_DD'])

print(f"Puhdistetussa datassa on {len(df)} kelvollista havaintoa.")

# ************************************************
# VAIHE 2: DATAN SUODATUS JA VALMISTELU TIIVISTEESEEN
# ************************************************

# 1. Määritellään aikaväli (Viimeiset 20 päivää)
viimeisin_paiva = df['Päivämäärä'].max().normalize() 
aloitus_paiva = viimeisin_paiva - timedelta(days=20) 

# Suodatetaan DataFrame
df_suodatettu = df[
    (df['Päivämäärä'].dt.normalize() >= aloitus_paiva) & 
    (df['Päivämäärä'].dt.normalize() <= viimeisin_paiva)
].copy()

# 2. Valmistellaan string-muotoon
levatilat = {
    0: "Ei levää",
    1: "Vähäinen määrä levää",
    2: "Runsaasti levää",
    3: "Erittäin runsaasti levää"
}
tiivistettava_data = df_suodatettu.copy()
tiivistettava_data['LevätilanneTxt'] = tiivistettava_data['LevätilanneNum'].map(levatilat)
tiivistettava_data = tiivistettava_data[[
    'Päivämäärä', 'Havaintopaikka', 'ELY-keskus', 'LevätilanneTxt'
]].sort_values(by='Päivämäärä', ascending=False)


# Tehdään koko datasta yksi pitkä, tiivis merkkijono
data_string = tiivistettava_data.to_string(index=False, header=True)

print(f"Viimeisen 20 päivän suodatettu data sisältää {len(df_suodatettu)} havaintoa.")

# ************************************************
# VAIHE 3: GEMINI API KUTSU JA TIIVISTE
# ************************************************

# Alustetaan Gemini-asiakas
try:
    # client etsii API-avaimen automaattisesti ympäristömuuttujasta (GEMINI_API_KEY)
    client = genai.Client(api_key="AIzaSyDPohCuJuJnFjRdaI1PMfPegDdyeyx121s")
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
3. Loppuhuomio: Sisällytä lyhyt yhteenveto havaintojen aikavälistä ({aloitus_paiva.strftime('%d.%m.%Y')} - {viimeisin_paiva.strftime('%d.%m.%Y')}).
4. Ohjeistus: Päätä tiedote lyhyeen ja ytimekkääseen ohjeistukseen toimenpiteistä sinilevän havaitsemisen varalle.

DATA ALKAA TÄSTÄ:
{data_string}
DATA PÄÄTTYY TÄHÄN.
"""

# 2. MALLIN KUTSU
print("\n" + "="*50)
print(f"Laaditaan sinilevätiedotetta aikavälille: {aloitus_paiva.strftime('%d.%m.%Y')} - {viimeisin_paiva.strftime('%d.%m.%Y')}")
print("="*50)

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

    print("\n" + "="*50)
    print("      VIIKOITTAINEN SINILEVÄTIEDOTE (TEKOÄLYN LAATIMA)      ")
    print("="*50)
    print(response.text)
    print("="*50)

except Exception as e:
    print(f"VIRHE Geminin kutsussa: {e}")