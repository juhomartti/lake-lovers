import pandas as pd
import numpy as np
import os
import joblib # Tarvitaan mallin lataamiseen
from sklearn.neighbors import NearestNeighbors
from xgboost import XGBClassifier
from typing import Dict, Any
import pathlib

# ************************************************
# ASETUKSET JA VAKIOT
# ************************************************
file_path = pathlib.Path().resolve() 
INPUT_FILE = os.path.join(file_path, 'api/util/rikastettu_sinileva_data.csv') 
MODEL_FILE = os.path.join(file_path, 'api/util/levamalli_xgboost.joblib') # Mallitiedosto

print(MODEL_FILE)

FEATURE_ORDER = [
    'Latitude_DD', 'Longitude_DD', 
    'Ilma_Lämpötila_7d_C', 'Sadanta_7d_mm', 'Tuuli_7d_ms', 
    'DayOfYear_sin', 'DayOfYear_cos', 'Vuosi'
]
RISKITASOT = {
    0: "Ei levää/Hyvä", 
    1: "Vähäinen levä", 
    2: "Kohtalainen levä", 
    3: "Runsasta levää"
}

# ************************************************
# 1. APUFUNKTIOT (Kopiotoitu pääohjelmasta)
# ************************************************

def hae_historialliset_keskiarvot(df_alkuperäinen: pd.DataFrame, lat: float, lon: float, kuukausi: int, k: int = 5) -> dict:
    """
    Hakee lähimmän k=5 pisteen sääpiirteiden (7d) kuukausikeskiarvot alkuperäisestä datasta.
    (HUOM: vaatii, että df_alkuperäinen sisältää jo DayOfYear_sin/cos sarakkeet)
    """
    # ... (Funktion sisältö on sama kuin edellisessä viestissäsi) ...
    
    # 1. Etsi K lähintä naapuria (Lähimmät Lat/Lon-pisteet datasta)
    mittauspisteet = df_alkuperäinen[['Latitude_DD', 'Longitude_DD']].drop_duplicates().copy()
    
    nn = NearestNeighbors(n_neighbors=k, algorithm='ball_tree').fit(mittauspisteet)
    distances, indices = nn.kneighbors([[lat, lon]])
    lähimmät_koordinaatit = mittauspisteet.iloc[indices[0]]
    
    # 2. Suodata data sijainnin ja kuukauden perusteella
    df_suodatettu_kuukausi = df_alkuperäinen[df_alkuperäinen['Päivämäärä'].dt.month == kuukausi].copy()
    
    # Valitaan rivit, joiden Lat/Lon täsmää lähimpiin pisteisiin
    lähimmät_latlon_parit = set(zip(lähimmät_koordinaatit['Latitude_DD'], lähimmät_koordinaatit['Longitude_DD']))
    
    df_tyypillinen = df_suodatettu_kuukausi[
        df_suodatettu_kuukausi.apply(lambda row: (row['Latitude_DD'], row['Longitude_DD']) in lähimmät_latlon_parit, axis=1)
    ].copy()
    
    # 3. Laske tyypilliset arvot
    if df_tyypillinen.empty or len(df_tyypillinen) < 5:
        df_tyypillinen = df_suodatettu_kuukausi.copy()
        print(f"VAROITUS: Ei riittävästi historiallista dataa lähimmiltä pisteiltä. Käytetään kuukauden {kuukausi} globaalia keskiarvoa.")

    tyypilliset_arvot = {
        'Ilma_Lämpötila_7d_C': df_tyypillinen['Ilma_Lämpötila_7d_C'].mean(),
        'Sadanta_7d_mm': df_tyypillinen['Sadanta_7d_mm'].mean(),
        'Tuuli_7d_ms': df_tyypillinen['Tuuli_7d_ms'].mean()
    }
    
    if np.isnan(tyypilliset_arvot['Ilma_Lämpötila_7d_C']):
          raise ValueError("Koulutusdatasta puuttuu kokonaan säädataa kyseiseltä kuukaudelta. Ennustetta ei voida laskea.")

    return tyypilliset_arvot

def ennusta_riski_koordinaatille(malli: XGBClassifier, df_alkuperäinen: pd.DataFrame, päivämäärä: str, sijainti: dict) -> dict:
    """
    Hakee ensin historialliset keskiarvot datasta ja tekee ennusteen.
    """
    try:
        pvm = pd.to_datetime(päivämäärä, format='%d.%m.%Y', errors='coerce')
        if pd.isna(pvm):
            pvm = pd.to_datetime(päivämäärä)
    except ValueError:
        return {"VIRHE": "Annettu päivämäärä on virheellisessä muodossa. Käytä esim. 'D.M.YYYY' tai 'YYYY-MM-DD'."}
        
    kuukausi = pvm.month
    
    # HAE TYP. ARVOT DATASTA
    try:
        tyypilliset_sääarvot = hae_historialliset_keskiarvot(df_alkuperäinen, sijainti['lat'], sijainti['lon'], kuukausi)
    except ValueError as e:
        return {"VIRHE": str(e)}

    # Piirteiden luonti
    DayOfYear = pvm.dayofyear
    DayOfYear_sin = np.sin(2 * np.pi * DayOfYear / 365)
    DayOfYear_cos = np.cos(2 * np.pi * DayOfYear / 365)
    vuosi = pvm.year
    
    # Luo DataFrame
    data = {
        'Latitude_DD': [sijainti['lat']], 
        'Longitude_DD': [sijainti['lon']], 
        'Ilma_Lämpötila_7d_C': [tyypilliset_sääarvot['Ilma_Lämpötila_7d_C']], 
        'Sadanta_7d_mm': [tyypilliset_sääarvot['Sadanta_7d_mm']], 
        'Tuuli_7d_ms': [tyypilliset_sääarvot['Tuuli_7d_ms']], 
        'DayOfYear_sin': [DayOfYear_sin], 
        'DayOfYear_cos': [DayOfYear_cos], 
        'Vuosi': [vuosi]
    }
    X_new = pd.DataFrame(data, columns=FEATURE_ORDER)
    
    # Ennustus
    ennuste_luokka = malli.predict(X_new)[0]
    ennuste_todennäköisyydet = malli.predict_proba(X_new)[0]
    
    # Tuloksen tulkinta
    return {
        "Sijainti": sijainti['nimi'],
        "Päivämäärä": pvm.strftime('%d.%m.%Y'),
        "Tyypilliset Arvot": tyypilliset_sääarvot,
        "Ennustettu Leväriski": RISKITASOT.get(ennuste_luokka, "Tuntematon riski"),
        "Todennäköisyydet": {RISKITASOT[i]: prob for i, prob in enumerate(ennuste_todennäköisyydet)}
    }

# ************************************************
# 2. PÄÄOHJELMA SUORITUS (Ennustus)
# ************************************************

def predict_func(date, lat, lon, name):
    print("Ladataan malli ja historiallinen data...")
    try:
        # Ladataan malli
        malli = joblib.load(MODEL_FILE)
        
        # Ladataan rikastettu data historiallisten arvojen hakua varten
        df_alkuperäinen = pd.read_csv(INPUT_FILE, sep=';')
        df_alkuperäinen['Päivämäärä'] = pd.to_datetime(df_alkuperäinen['Päivämäärä'], errors='coerce')
        df_alkuperäinen['DayOfYear'] = df_alkuperäinen['Päivämäärä'].dt.dayofyear
        
        # Laske sin/cos, koska malli tarvitsee niitä
        df_alkuperäinen['DayOfYear_sin'] = np.sin(2 * np.pi * df_alkuperäinen['DayOfYear'] / 365)
        df_alkuperäinen['DayOfYear_cos'] = np.cos(2 * np.pi * df_alkuperäinen['DayOfYear'] / 365)
        
        # Puhdista puuttuvista sää/levä-tiedoista.
        df_alkuperäinen = df_alkuperäinen.dropna(subset=['Ilma_Lämpötila_7d_C', 'Sadanta_7d_mm', 'Tuuli_7d_ms', 'LevätilanneNum']).copy()

    except FileNotFoundError as e:
        print(f"VIRHE: Vaadittu tiedostoa ei löytynyt: {e}")
        print("Varmista, että olet ajanut koulutusskriptin ja että tiedostot ovat oikeassa paikassa.")
        exit()

    # KÄYTTÄJÄN SYÖTE: Pielavesi/Lahdenpohja
    ENNUSTE_PVM = date
    ENNAKOITU_SIJAINTI = {
        'nimi': name,
        'lat': lat, 
        'lon': lon
    }

    tulos = ennusta_riski_koordinaatille(malli, df_alkuperäinen, ENNUSTE_PVM, ENNAKOITU_SIJAINTI)
    
    print("\n" + "="*50)
    print(" ENNAKOITU LEVÄRISKI (Dynaaminen Haku)")
    print("="*50)

    if "VIRHE" in tulos:
        print(tulos["VIRHE"])
    else:
        print(f"Sijainti: **{tulos['Sijainti']}**")
        print(f"Päivämäärä: {tulos['Päivämäärä']}")
        print(f"Käytetyt sääarvot (hist. 7d keskiarvot kuukaudelle): {tulos['Tyypilliset Arvot']}")
        print(f"\n=> Ennustettu Leväriski: **{tulos['Ennustettu Leväriski']}**")
        print("\nTodennäköisyydet luokittain:")
        for riski, prob in tulos['Todennäköisyydet'].items():
            print(f"   - {riski}: {prob*100:.2f}%")
    print("="*50)
    return tulos