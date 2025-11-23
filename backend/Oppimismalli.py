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
import seaborn as sns

# ************************************************
# ASETUKSET JA VAKIOT
# ************************************************
file_path = "C:\\Users\\35845\\Documents\\PYTHON\\Hackhaton\\" 
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


import matplotlib.pyplot as plt

def analysoi_piirteiden_merkitys(malli: XGBClassifier):
    """Laskee ja visualisoi piirteiden merkityksen XGBoost-mallissa."""
    print("\n--- PIIRTEIDEN MERKITYS (FEATURE IMPORTANCE) ---")
    
    # Hae piirteiden merkitys (Importance)
    importances = malli.feature_importances_
    feature_names = malli.get_booster().feature_names
    
    # Luo DataFrame visualisointia varten
    feature_importance_df = pd.DataFrame({
        'Piirre': feature_names,
        'Merkitys': importances
    }).sort_values(by='Merkitys', ascending=False)
    
    # Tulosta Top 5 tärkeintä piirrettä
    print(feature_importance_df.head(5))
    
    # Visualisoi
    plt.figure(figsize=(10, 6))
    plt.barh(feature_importance_df['Piirre'], feature_importance_df['Merkitys'], color='skyblue')
    plt.xlabel('Piirteen Merkitys (F-score)')
    plt.title('XGBoost - Piirteiden merkitys sinileväennustuksessa')
    plt.gca().invert_yaxis()
    plt.show()

def visualisoi_vuosittainen_kehitys(df: pd.DataFrame):
    """Visualisoi levähavaintojen jakautumisen vuosittain."""
    print("\n--- VUOSITTAINEN KEHITYS JA TEKIJÄT ---")
    
    # Levätilanteen jakautuminen vuosittain
    df['Levätilanne'] = df['LevätilanneNum'].map(RISKITASOT)
    
    plt.figure(figsize=(12, 6))
    sns.countplot(x='Vuosi', hue='Levätilanne', data=df, palette="viridis", 
                  order=sorted(df['Vuosi'].unique()))
    plt.title('Levätilanteiden jakautuminen vuosittain (2021-2025)')
    plt.xlabel('Vuosi')
    plt.ylabel('Havaintojen lukumäärä')
    plt.legend(title='Levätilanne')
    plt.show()

def visualisoi_lampotila_ja_levä(df: pd.DataFrame):
    """Visualisoi DayOfYear, lämpötilan ja korkean leväriskin suhteen."""
    
    # Etsitään päivät, joina on ollut runsasta (tai kohtalaista) levää (esim. LevätilanneNum >= 2)
    df_high_risk = df[df['LevätilanneNum'] >= 2]
    
    plt.figure(figsize=(14, 7))
    
    # Kaikki lämpötilapisteet (läpinäkyvänä)
    sns.scatterplot(x='DayOfYear', y='Ilma_Lämpötila_7d_C', data=df, 
                    alpha=0.2, label='Kaikki havainnot (7d lämpötila)', color='gray')
    
    # Korkean riskin lämpötilat (selkeästi näkyvinä)
    sns.scatterplot(x='DayOfYear', y='Ilma_Lämpötila_7d_C', data=df_high_risk, 
                    hue='Levätilanne', palette='Reds', size='LevätilanneNum', sizes=(50, 200), 
                    label='Korkean leväriskin havainnot', legend='full')
    
    plt.title('Leväriski vs. 7 päivän keskilämpötila vuodenpäivän mukaan')
    plt.xlabel('Vuodenpäivä (1-365)')
    plt.ylabel('Keskilämpötila 7d [°C]')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.show()


    import seaborn as sns
import matplotlib.pyplot as plt

def visualisoi_kausivaihtelu(df: pd.DataFrame):
    """Visualisoi levähavaintojen jakautumisen vuodenpäivän mukaan."""
    
    # Valitaan vain korkean riskin havainnot (esim. Kohtalainen ja Runsas, LevätilanneNum >= 2)
    df_high_risk = df[df['LevätilanneNum'] >= 2].copy()
    
    # Päivämäärän muuntaminen Month-Day-muotoon (vain visualisointia varten)
    df_high_risk['KuukausiPäivä'] = df_high_risk['Päivämäärä'].dt.strftime('%m-%d')
    
    plt.figure(figsize=(15, 7))
    
    # Käytetään DayOfYear-saraketta (1-365) x-akselilla
    sns.histplot(df_high_risk['DayOfYear'], bins=180, kde=False, color='#2c7bb6') # n. 2 päivän välein
    
    plt.title('Korkean leväriskin (Kohtalainen/Runsas) havaintojen ajoittuminen')
    plt.xlabel('Vuodenpäivä (1-365)')
    plt.ylabel('Korkean riskin havaintojen lukumäärä')
    
    # Lisätään kuukausien etiketit (likimääräiset DayOfYear-arvot)
    plt.xticks([31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335], 
               ['Tammi', 'Maalis', 'Huhti', 'Touko', 'Kesä', 'Heinä', 'Elo', 'Syys', 'Loka', 'Marras', 'Joulu'])
    
    plt.axvspan(152, 244, color='red', alpha=0.1, label='Kesän leväkausi (Kesä-Elo)')
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.xlim(100, 300) # Rajataan näkymä Huhtikuusta Lokakuuhun
    plt.show()

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

        
        analysoi_piirteiden_merkitys(malli)
        visualisoi_vuosittainen_kehitys(df_alkuperäinen)
        visualisoi_lampotila_ja_levä(df_alkuperäinen)
        visualisoi_kausivaihtelu(df_alkuperäinen)