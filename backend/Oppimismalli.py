import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder
from sklearn.neighbors import NearestNeighbors
import os
import joblib 
from typing import Dict, Any, Tuple

# ************************************************
# ASETUKSET JA VAKIOT
# ************************************************
file_path = "." 
INPUT_FILE = os.path.join(file_path, 'rikastettu_sinileva_data.csv') 
MODEL_FILE = os.path.join(file_path, 'levamalli_xgboost.joblib')

# Piirteiden järjestys (kriittinen ennustuksessa)
FEATURE_ORDER = [
    'Latitude_DD', 'Longitude_DD', 
    'Ilma_Lämpötila_7d_C', 'Sadanta_7d_mm', 'Tuuli_7d_ms', 
    'DayOfYear_sin', 'DayOfYear_cos', 'Vuosi'
]

# Leväriskin tulkinta
RISKITASOT = {
    0: "Ei levää/Hyvä", 
    1: "Vähäinen levä", 
    2: "Kohtalainen levä", 
    3: "Runsasta levää"
}

# ************************************************
# 1. DATAN LATAUS JA JAKA
# ************************************************
# (lataa_rikastettu_data_ja_jaa -funktio pysyy samana, mutta varmista, että siinä on ne sin/cos-laskennat!)

def lataa_rikastettu_data_ja_jaa():
    """Lataa rikastetun datan ja jakaa sen 60/20/20 osiin."""
    try:
        df = pd.read_csv(INPUT_FILE, sep=';')
        df['Päivämäärä'] = pd.to_datetime(df['Päivämäärä'], errors='coerce')
        df['DayOfYear'] = df['Päivämäärä'].dt.dayofyear
        df['Vuosi'] = df['Päivämäärä'].dt.year
        df['DayOfYear_sin'] = np.sin(2 * np.pi * df['DayOfYear'] / 365) # LISÄTTY
        df['DayOfYear_cos'] = np.cos(2 * np.pi * df['DayOfYear'] / 365) # LISÄTTY

        df = df.dropna(subset=['Ilma_Lämpötila_7d_C', 'Sadanta_7d_mm', 'Tuuli_7d_ms', 'LevätilanneNum']).copy()
        
        X = df[FEATURE_ORDER]
        y = df['LevätilanneNum']
        
        le = LabelEncoder()
        y = le.fit_transform(y)
        
        # ... (Jako pysyy samana) ...
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=0.25, random_state=42, stratify=y_temp
        )
        
        print(f"\n--- DATAN JAKO ---")
        print(f"Rikastettu data ladattu: {len(df)} riviä.")
        print(f"Koulutusdata (Train): {len(X_train)} ({len(X_train)/len(df):.0%})")
        print(f"Validointidata (Validation): {len(X_val)} ({len(X_val)/len(df):.0%})")
        print(f"Testidata (Test): {len(X_test)} ({len(X_test)/len(df):.0%})")
        
        return X_train, X_val, X_test, y_train, y_val, y_test, df
        
    except FileNotFoundError:
        print(f"FATAL VIRHE: Tiedostoa {INPUT_FILE} ei löytynyt. Varmista, että datan rikastus-skripti on ajettu.")
        return None

# ************************************************
# 2. XGBOOST KOULUTUS JA VALIDIOINTI
# ************************************************

def kouluta_ja_validoi_xgboost(X_train: pd.DataFrame, X_val: pd.DataFrame, y_train: np.ndarray, y_val: np.ndarray) -> XGBClassifier:
    """Kouluttaa XGBoost-mallin."""
    # (Funktio pysyy samana)
    num_classes = len(np.unique(y_train))
    print(f"\nHavaittu luokkien lukumäärä koulutusdatassa (num_class): {num_classes}")

    model = XGBClassifier(
        objective='multi:softmax',
        num_class=num_classes, 
        eval_metric='mlogloss', 
        n_estimators=500,
        learning_rate=0.05,
        max_depth=6,
        random_state=42
    )
    
    model.fit(X_train, y_train, verbose=False)
    
    val_score = model.score(X_val, y_val)
    print(f"\nKoulutus valmis. Mallin tarkkuus validointidatalla (Accuracy): {val_score:.4f}")
    
    return model

# ************************************************
# UUSI: 2B. MALLIN TALLENNUS
# ************************************************

def tallenna_malli(malli: XGBClassifier, tiedostonimi: str):
    """Tallentaa koulutetun mallin joblib-muotoon levylle."""
    try:
        joblib.dump(malli, tiedostonimi)
        print(f"MALLI TALLENNETTU ONNISTUNEESTI tiedostoon: {os.path.basename(tiedostonimi)}")
    except Exception as e:
        print(f"VIRHE MALLIN TALLENTAMISESSA: {e}")

# ************************************************
# 5. PÄÄOHJELMA SUORITUS
# ************************************************

if __name__ == "__main__":
    
    # 1. Ladataan data ja tehdään jako
    jaetut_tiedot = lataa_rikastettu_data_ja_jaa()
    
    if jaetut_tiedot:
        X_train, X_val, X_test, y_train, y_val, y_test, df_alkuperäinen = jaetut_tiedot
        
        # 2. Kouluta malli
        malli = kouluta_ja_validoi_xgboost(X_train, X_val, y_train, y_val)
        
        # 2B. UUSI VAIHE: TALLENNA MALLI
        tallenna_malli(malli, MODEL_FILE)
        
        # 3. Testi-data arvioidaan lopuksi
        test_predictions = malli.predict(X_test)
        test_score = accuracy_score(y_test, test_predictions)
        print(f"\nLopullinen arvio (Testi Data Accuracy): {test_score:.4f}")

# HUOM: Ennustuslogiikka on poistettu tästä tiedostosta!
# Ennustusfunktiot (hae_historialliset_keskiarvot ja ennusta_riski_koordinaatille)
# siirretään ennustaja.py -tiedostoon.