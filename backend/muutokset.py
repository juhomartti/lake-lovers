import pandas as pd
import re
from datetime import timedelta, date
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv # Tuotu .env-tiedoston lukemiseksi

# ************************************************
# ASETUKSET
# ************************************************

# Aseta TÄYDELLINEN polku sinun result.csv tiedostoosi
file_path = "C:\\Users\\35845\\Documents\\PYTHON\\Hackhaton\\result.csv" 

# ************************************************
# APUFUNKTIOT
# ************************************************

def dms_to_dd(dms_str):
    """ Muuntaa koordinaattimerkkijonon (DMS) desimaaliasteiksi (DD). """
    if not isinstance(dms_str, str): return None
    match = re.search(r'(\d+)\D+(\d+)\D+([\d\.]+)\D+([NnSsEeWw])', dms_str)
    if match:
        degrees = float(match.group(1)); minutes = float(match.group(2))
        seconds = float(match.group(3)); direction = match.group(4).upper()
        decimal_degrees = degrees + minutes / 60 + seconds / 3600
        if direction in ('S', 'W'): decimal_degrees *= -1
        return decimal_degrees
    return None

# ************************************************
# VAIHE 1: DATAN LUKU JA PUHDISTUS
# ************************************************

def lue_ja_puhdista_data(file_path):
    """Lukee, puhdistaa ja muuntaa koordinaatit sekä päivämäärät."""
    try:
        df = pd.read_csv(file_path, sep=';', encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, sep=';', encoding='iso-8859-1')
    except FileNotFoundError:
        print(f"VIRHE: Tiedostoa ei löytynyt polusta: {file_path}")
        return None

    # Muunnokset
    df['Koordinaatit_Clean'] = df['Koordinaatit'].str.replace('"', '').str.strip()
    df[['Leveysaste_DMS', 'Pituusaste_DMS']] = df['Koordinaatit_Clean'].str.split(',', expand=True)
    df['Latitude_DD'] = df['Leveysaste_DMS'].apply(dms_to_dd)
    df['Longitude_DD'] = df['Pituusaste_DMS'].apply(dms_to_dd)
    df['Päivämäärä'] = pd.to_datetime(df['Päivämäärä'], errors='coerce')

    # Siivous
    df = df.drop(columns=['Koordinaatit', 'Koordinaatit_Clean', 'Leveysaste_DMS', 'Pituusaste_DMS'])
    df = df.dropna(subset=['Päivämäärä', 'Latitude_DD', 'Longitude_DD', 'LevätilanneNum'])
    
    print(f"Puhdistetussa datassa on {len(df)} kelvollista havaintoa.")
    return df

# ************************************************
# TOIMINTO 1: GLOBAALI VIIKKOTIEDOTE
# ************************************************

def laadi_viikkotiedote(df, client):
    """Suodattaa viimeisen 20 päivän datan ja luo globaalin viikkotiedotteen."""
    
    viimeisin_paiva = df['Päivämäärä'].max().normalize() 
    aloitus_paiva = viimeisin_paiva - timedelta(days=20) 
    df_suodatettu = df[
        (df['Päivämäärä'].dt.normalize() >= aloitus_paiva) & 
        (df['Päivämäärä'].dt.normalize() <= viimeisin_paiva)
    ].copy()

    if df_suodatettu.empty:
        print("Ei havaintoja viimeisen 20 päivän ajalta. Tiedotetta ei voida laatia.")
        return

    levatilat = {0: "Ei levää", 1: "Vähäinen määrä levää", 2: "Runsaasti levää", 3: "Erittäin runsaasti levää"}
    tiivistettava_data = df_suodatettu.copy()
    tiivistettava_data['LevätilanneTxt'] = tiivistettava_data['LevätilanneNum'].map(levatilat)

    tiivistettava_data = tiivistettava_data[['Päivämäärä', 'Havaintopaikka', 'ELY-keskus', 'LevätilanneTxt', 'Lisätiedot']]
    tiivistettava_data['Lisätiedot'] = tiivistettava_data['Lisätiedot'].fillna('Ei lisätietoja.')
    tiivistettava_data = tiivistettava_data.sort_values(by='Päivämäärä', ascending=False)
    data_string = tiivistettava_data.to_string(index=False, header=True)
    
    print(f"Viimeisen 20 päivän suodatettu data sisältää {len(df_suodatettu)} havaintoa.")
# Lisätään nykyinen päivämäärä tiedoksi

    # PROMPT ENGINEERING
    system_prompt = ("Olet Suomen Ympäristökeskuksen (SYKE) asiantuntija ja laadit virallisia sinilevätiedotteita. "
        "Tuota analyyttinen ja yleistajuinen raportti annetusta datasta. **Käytä Lisätiedot-sarakkeen sisältöä (jos se ei ole tyhjä) antamaan laadullista lisätietoa havainnoista.** "
        "Vastaa AINOASTAAN suomeksi, yhtenäisenä, tyyliltään virallista tiedotetta muistuttavana raporttina, jossa ei ole numeroituja luetteloita. Maksimipituus 400 sanaa. **Älä toista samaa informaatiota.**"
    )
    
    tanaan = date.today().strftime('%d.%m.%Y')
    user_prompt = f"""Tämänhetkinen päivämäärä on: {tanaan}.
    Analysoi alla oleva 20 viimeisimmän päivän sinilevähavaintoja koskeva data ja laadi siitä tiivis, viikoittaista sinilevätiedotetta vastaava yhteenveto. 
    Enemmän painoarvoa on viimeisimmillä havainnoilla mutta huomioi miten sinilevä tilanteet voi muuttua ja mahdollisesti pysyä.
    Muodosta tiedote kolmeen yhtenäiseen pääkappaleeseen:
    1.  **Yleistilanne ja yhteenveto:** Aloita tiivistelmän yleiskuvauksella havaintojen aikaväliltä ({aloitus_paiva.strftime('%d.%m.%Y')} - {viimeisin_paiva.strftime('%d.%m.%Y')}). Kerro, kuinka monessa havainnossa levää havaittiin (LevätilanneTxt != "Ei levää") ja kuinka monessa havaittiin runsas/erittäin runsas esiintymä.
    2.  **Alueellinen katsaus ja laadullinen tieto:** Kuvaile ne ELY-keskusten alueet (2-3 keskeisintä) ja vesistöt, joissa runsaita tai erittäin runsaita leväesiintymiä havaittiin eniten. **Sisällytä havaintoihin liittyvät Lisätiedot-sarakkeen laadulliset huomiot luontevasti tähän osioon.** Mainitse havainnot paikoittain tarkasti (esim. järven nimi).
    3.  **Toimenpideohjeistus:** Päätä tiedote lyhyeen ja ytimekkääseen ohjeistukseen siitä, mitä toimenpiteitä sinilevän havaitseminen vaatii.
    DATA ALKAA TÄSTÄ:
    {data_string}
    DATA PÄÄTTYY TÄHÄN."""

    # MALLIN KUTSU
    print("\n" + "="*50)
    print(f"LAADITAAN GLOBAALI VIIKKOTIEDOTE AIKAVÄLILLE: {aloitus_paiva.strftime('%d.%m.%Y')} - {viimeisin_paiva.strftime('%d.%m.%Y')}")
    print("="*50)

    config = types.GenerateContentConfig(system_instruction=system_prompt, temperature=0.2)
    try:
        response = client.models.generate_content(model='gemini-2.5-flash', contents=user_prompt, config=config)
        print("\n" + "="*50)
        print("      VIIKOITTAINEN SINILEVÄTIEDOTE (TEKOÄLYN LAATIMA)      ")
        print("="*50)
        print(response.text)
        print("="*50)
    except Exception as e:
        print(f"VIRHE Geminin kutsussa: {e}")

# ************************************************
# APUFUNKTIOT
# ************************************************

# Haversine-funktio etäisyyden laskemiseen
def haversine_distance(lat1, lon1, lat2, lon2):
    """ Laskee etäisyyden kahden GPS-pisteen välillä (km). """
    import numpy as np # Käyttää numpy-kirjastoa
    R = 6371 # Maan säde kilometreissä
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

# ************************************************
# TOIMINTO 2: PAIKALLINEN ANALYYSI <-- KOORDINAATTIHAKU
# ************************************************

# FUNKTION ALLEKIRJOITUS MUUTETTU! Nyt tarvitaan Lat ja Lon.
def analysoi_paikallisesti(df, klikattu_lat, klikattu_lon, client, sade_km=10):
    """
    Analysoi sinilevätilanteen koordinaattien perusteella (10 km säde).
    """
    # MÄÄRITETÄÄN NYKYPÄIVÄMÄÄRÄ
    # tanaan = date.today().strftime('%d.%m.%Y')

    # Laske etäisyys klikatusta pisteestä kaikkiin DataFrame-pisteisiin
    distances = haversine_distance(df['Latitude_DD'], df['Longitude_DD'], klikattu_lat, klikattu_lon)
    
    # Suodata havainnot säteen perusteella
    df_paikallinen = df[distances <= sade_km].copy()

    if df_paikallinen.empty:
        print(f"\n---> VIRHE: Havaintoja ei löytynyt {sade_km} km säteeltä koordinaateista ({klikattu_lat:.2f}, {klikattu_lon:.2f}).")
        return

    # Määritä lähimmän havainnon nimi otsikkoa varten
    laimpaan_indeksi = distances.idxmin()
    viimeisin_havainto = df_paikallinen.sort_values(by='Päivämäärä', ascending=False).iloc[0]
    
    # Käytä lähimmän havainnon nimeä kohteena, jotta tiivistelmässä on järven nimi
    puhdas_lähin_nimi = re.sub(r'\s*\([\d\.]+\)', '', df.loc[laimpaan_indeksi, 'Havaintopaikka']).strip()
    
    # --- LLM:lle lähetettävät tiedot ---
    
    # Laske historiallinen data LLM:lle lähetettäväksi
    historiallinen_data = df_paikallinen.sort_values(by='Päivämäärä', ascending=False).head(10).copy()
    historiallinen_sinilevatilanne = "Viimeiset 10 havaintoa (uudemmasta vanhempaan, LevätilanneNum 0-3):\n" + historiallinen_data[['Päivämäärä', 'LevätilanneNum']].to_string(index=False)

    levatilat = {0: "Ei levää", 1: "Vähäinen määrä levää", 2: "Runsaasti levää", 3: "Erittäin runsaasti levää"}
    viimeisin_levatila = levatilat.get(viimeisin_havainto['LevätilanneNum'], "Tuntematon")

    # 2: UUSI JÄRJESTELMÄVIESTI
    system_prompt = (
        "Olet vesistöasiantuntija. Laadi lyhyt, informatiivinen yhteenveto annetun vesistön sinilevätilanteesta. "
        "**Perustele vesistön laatu (LevätilanneNum) ja sinilevätilanteen tyypillisyys (poikkeuksellisuus) annettujen historiallisten havaintojen perusteella, erityisesti päivämääriin ja LevätilanneNum-arvoihin nojautuen.** "
        "LevätilanneNum-arvoihin liittyvät merkitykset ovat: 0 = Ei levää, 1 = Vähäinen määrä levää, 2 = Runsaasti levää, 3 = Erittäin runsaasti levää, älä käytä numeroita sellaisenaan vaan merkityksi. "
        "Käytä netistä löytyviä luotettavia lähteitä tarvittaessa taustatiedon tarkistamiseen, kuten jos viimeisimmästä havainnosta on pitkä aika on levätilanne luultavasti muuttunut. "
        "Tarkoitus on tietää millainen tilanne vesistössä on sinilevän osalta TÄLLÄ HETKELLÄ. "
        "Vastaa AINOASTAAN suomeksi. Maksimi 150 sanaa."
    )

    # MUUTOS 3: UUSI KÄYTTÄJÄVIESTI (Siivottu turhista muuttujista)
    tanaan = date.today().strftime('%d.%m.%Y')
    user_prompt = f"""
Laadi tiivistelmän otsikko ainoastaan muodossa '**{puhdas_lähin_nimi} ({sade_km} km säde) – Sinilevätilanne**'.

Tee tiivistelmä alueen '{puhdas_lähin_nimi}' lähialueen havainnoista.

- **Tämänhetkinen Päivämäärä:** {tanaan}
- **Alueen Viimeisin Havainto:** {viimeisin_havainto['Havaintopaikka']} ({viimeisin_havainto['Päivämäärä'].strftime('%d.%m.%Y')}), Levätilanne: {viimeisin_levatila}.
- **Viimeisimmän havainnon Lisätiedot:** {viimeisin_havainto['Lisätiedot'] if pd.notna(viimeisin_havainto['Lisätiedot']) else 'Ei lisätietoja.'}
- **Viimeisimmän havainnon LevätilanneNum:** {viimeisin_havainto['LevätilanneNum']}
- **Historiallinen Levätilanne (Viimeiset 10 kpl alueelta):**
{historiallinen_sinilevatilanne}
- **Koko datamäärä haetulta alueelta:** {len(df_paikallinen)} havaintoa.
- **HUOMIO: Tämänhetkinen päivämäärä on {tanaan}. Huomioi, miten pitkä aika on kulunut viimeisimmästä havainnosta ({viimeisin_havainto['Päivämäärä'].strftime('%d.%m.%Y')}) ja tee paras veikkaus TÄMÄN HETKISEN levätilanteen osalta. Esimerkiksi syksyllä/talvella vanhat havainnot eivät ole enää luotettavia.**

Laadi yhteenveto, jossa kerrot: 
1. Kohteen tämänhetkisen sinilevätilanteen (viimeisin havainto, huomioiden veikkauksen ajankohdan muutoksen vuoksi).
2. Arvioi vesistön sinilevätilanteen tyypillisyyden / poikkeuksellisuuden (esim. onko tilanne pysyvä, poikkeuksellisen runsas/matala tai esiintyykö levää harvinaiseen aikaan) perustuen annettuihin historiallisiin tietoihin.
3. Huomioi ajan muutos ja mahdollinen levätilanteen kehitys.
4. Perustuen Lisätietoihin, mainitse kaikki laadulliset havainnot. 
5. Annat lyhyen suosituksen käyttäytymisestä sinilevän esiintyessä.
"""

    # MALLIN KUTSU
    config = types.GenerateContentConfig(system_instruction=system_prompt, temperature=0.2)
    
    print("\n" + "="*50)
    print(f"LAADITAAN PAIKALLISTA ANALYYSIA KOORDINAATEILLE: ({klikattu_lat:.2f}, {klikattu_lon:.2f})")
    print("="*50)

    try:
        response = client.models.generate_content(model='gemini-2.5-flash', contents=user_prompt, config=config)
        print(response.text)
        print("="*50)
    except Exception as e:
        print(f"VIRHE Geminin kutsussa: {e}")

# ************************************************
# PÄÄOHJELMA
# ************************************************

if __name__ == "__main__":

        # LADATAAN YMPÄRISTÖMUUTTUJAT .env-TIEDOSTOSTA
        load_dotenv()

        # LUETAAN JA PUHDISTETAAN DATA
        df_puhdistettu = lue_ja_puhdista_data(file_path)

        if df_puhdistettu is not None:
            # ALUSTETAAN GEMINI-ASIAKAS
            try:
                client = genai.Client()
            except Exception as e:
                print(f"\nVIRHE API-avaimen alustuksessa. Varmista, että 'GEMINI_API_KEY' on asetettu .env-tiedostoon ja se on kelvollinen.")
                exit()

            # 4. AJA GLOBAALI VIIKKOTIEDOTE
            laadi_viikkotiedote(df_puhdistettu, client)

            # 5. AJA PAIKALLINEN ANALYYSI (KOORDINAATEILLA)
            print("\n" + "="*50)
            print("KÄYNNISTETÄÄN PAIKALLISET ANALYYSIT (KOORDINAATEILLA)")
            print("="*50)

            # Esimerkki: Pielavesi/Lahdenpohja koordinaateilla (Lat: 63.243, Lon: 26.7252)
            # Säteeksi asetettu 10 km
            analysoi_paikallisesti(df_puhdistettu, 63.243, 26.7252, client, sade_km=10)