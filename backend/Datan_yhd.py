import pandas as pd
import re
from datetime import timedelta, date, datetime
import os
import glob
import requests
import numpy as np
from io import StringIO
import time 
from dotenv import load_dotenv
from typing import Tuple, Optional 

# ************************************************
# ASETUKSET
# ************************************************

# Oletuspolku on nyt kova-koodattu, mutta HUOM! Varmista, että tiedostosi ovat TÄSSÄ kansiossa.
file_path = "C:\\Users\\35845\\Documents\\PYTHON\\Hackhaton\\" 
OUTPUT_FILE = os.path.join(file_path, 'rikastettu_sinileva_data.csv') 
USE_PARQUET = False

# ************************************************
# APUFUNKTIOT
# ************************************************

def dms_to_dd(dms_str):
    """ Muuntaa koordinaattimerkkijonon (DMS) desimaaliasteiksi (DD). """
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

def hae_openmeteo_lampotila(latitude: float, longitude: float, target_date: datetime, days_before: int = 7) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[pd.DataFrame]]:
    """
    Hakee päivittäisen lämpötilan, sadannan ja tuulen 7 päivän ajalta 
    Open-Meteo API:sta ja laskee niistä 7 päivän keskiarvot/summat.
    """
    
    end_date = target_date.strftime('%Y-%m-%d')
    start_date = (target_date - timedelta(days=days_before - 1)).strftime('%Y-%m-%d')
    
    url = 'https://archive-api.open-meteo.com/v1/archive'
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'start_date': start_date,
        'end_date': end_date,
        'daily': 'temperature_2m_mean,precipitation_sum,wind_speed_10m_mean', 
        'timezone': 'auto'
    }
    
    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        daily = data.get('daily', {})
        dates = daily.get('time')
        daily_temps = daily.get('temperature_2m_mean')
        daily_precip = daily.get('precipitation_sum') 
        daily_wind = daily.get('wind_speed_10m_mean')

        if daily_temps and dates and daily_precip and daily_wind and isinstance(daily_temps, list):
            
            # Lämpötilan ja tuulen nopeuden keskiarvot
            avg_temp = pd.Series(daily_temps).mean()
            avg_wind_speed = pd.Series(daily_wind).mean()
            
            # Sadannan summa
            total_precip = pd.Series(daily_precip).sum()

            daily_data = pd.DataFrame({
                'Päivämäärä': dates, 
                'Lämpötila_C': daily_temps,
                'Sadanta_mm': daily_precip,
                'Tuulen_nopeus_ms': daily_wind
            })
            
            return avg_temp, total_precip, avg_wind_speed, daily_data
        else:
            return None, None, None, None
            
    except requests.exceptions.RequestException as e:
        # print(f"API-VIRHE sijainnille {latitude}, {longitude}: {e}") # Piilotettu tulostus
        return None, None, None, None
    except Exception as e:
        print(f"Yleinen virhe: {e}")
        return None, None, None, None

# ************************************************
# VAIHE 1 & 2: DATAN LUKU JA PUHDISTUS
# ************************************************

def lue_ja_yhdistä_data(data_dir):
    """Etsii kaikki HavaintoXX.csv tiedostot kansiosta, lukee ja yhdistää ne yhdeksi DataFrameksi."""
    # MUUTETTU: Etsii kaikki Havainto[kaksi numeroa].csv tiedostot, esim. Havainto21.csv - Havainto99.csv
    all_files = glob.glob(os.path.join(data_dir, "Havainto[0-9][0-9].csv")) 
    
    # KORJAUS: TARKISTA ETTÄ JOSSAKIN ON 5 TIEDOSTOA, MUUTEN KÄYTÄ KAIKKI
    if not all_files:
        print(f"VIRHE: Tiedostoja 'HavaintoXX.csv' ei löytynyt polusta: {data_dir}")
        return None
        
    df_list = []
    
    # Suodatetaan pois muut kuin "HavaintoXX.csv" (esim. rikastu_sinileva_data.csv)
    target_files = [f for f in all_files if re.match(r'.*Havainto\d\d\.csv$', f, re.IGNORECASE)]
    
    for filename in target_files:
        try: df = pd.read_csv(filename, sep=';', encoding='utf-8')
        except UnicodeDecodeError: df = pd.read_csv(filename, sep=';', encoding='iso-8859-1')
        except Exception: continue
        df_list.append(df)
        
    if not df_list:
        print("VIRHE: Yhtään kelvollista CSV-tiedostoa ei voitu lukea.")
        return None
        
    df_yhdistetty = pd.concat(df_list, ignore_index=True)
    print(f"Kaikki {len(df_list)} tiedostoa yhdistetty. Yhteensä {len(df_yhdistetty)} riviä.")
    return df_yhdistetty

def puhdista_ja_muunna_data(df):
    """Muuntaa koordinaatit, päivämäärät ja siivoaa datan ennustemalleja varten."""
    print("\n--- Datan puhdistus ja muunnos ---")
    df['Päivämäärä'] = pd.to_datetime(df['Päivämäärä'], errors='coerce').dt.normalize()
    
    if 'Koordinaatit' in df.columns:
        df['Koordinaatit_Clean'] = df['Koordinaatit'].str.replace('"', '').str.strip()
        split_coords = df['Koordinaatit_Clean'].str.split(',', expand=True)
        
        if split_coords.shape[1] >= 2:
            df[['Leveysaste_DMS', 'Pituusaste_DMS']] = split_coords.iloc[:, :2]
            
        df['Latitude_DD'] = df['Leveysaste_DMS'].apply(dms_to_dd)
        df['Longitude_DD'] = df['Pituusaste_DMS'].apply(dms_to_dd)
        
        df = df.drop(columns=[col for col in ['Koordinaatit', 'Koordinaatit_Clean', 'Leveysaste_DMS', 'Pituusaste_DMS'] if col in df.columns], errors='ignore')
        
    df['LevätilanneNum'] = pd.to_numeric(df['LevätilanneNum'], errors='coerce')
    
    # Puhdistus - vaaditaan LevätilanneNum, Päivämäärä, ja DD-koordinaatit
    df_puhdistettu = df.dropna(subset=['Päivämäärä', 'Latitude_DD', 'Longitude_DD', 'LevätilanneNum']).copy()
    
    # Ajalliset muuttujat
    df_puhdistettu['Vuosi'] = df_puhdistettu['Päivämäärä'].dt.year
    df_puhdistettu['DayOfYear'] = df_puhdistettu['Päivämäärä'].dt.dayofyear
    
    print(f"Puhdistetussa ja muunnetussa datassa on {len(df_puhdistettu)} kelvollista havaintoa.")
    return df_puhdistettu

# ************************************************
# VAIHE 3: LÄMPÖTILAN, SADANNAN JA TUULEN LIITTÄMINEN
# ************************************************

def liita_openmeteo_lampotilat(df_sinileva):
    """Iteroi sinilevädataa ja hakee Open-Meteo säämuuttujien 7 päivän keskiarvot/summat."""
    print("\n--- Haetaan Ilman Lämpötilan, Sadannan ja Tuulen 7 päivän Keskiarvot/Summat ---")
    
    df_temp = df_sinileva.copy() 
    df_temp['Ilma_Lämpötila_7d_C'] = np.nan
    df_temp['Sadanta_7d_mm'] = np.nan
    df_temp['Tuuli_7d_ms'] = np.nan 
    
    daily_data_list = []
    
    # Määritä käsiteltyjen rivien kokonaismäärä
    total_rows = len(df_temp)
    
    for index, row in df_temp.iterrows():
        
        # Tulostetaan tilannepäivitys
        current_row_number = df_temp.index.get_loc(index) + 1
        if current_row_number % 100 == 0 or current_row_number == total_rows:
            print(f"Käsitellään riviä {current_row_number}/{total_rows}...")

        # Haku API:sta
        avg_temp, total_precip, avg_wind_speed, daily_df = hae_openmeteo_lampotila(
            row['Latitude_DD'], 
            row['Longitude_DD'], 
            row['Päivämäärä'], 
            days_before=7
        )
        
        if avg_temp is not None:
            # Sijoita kaikki kolme arvoa
            df_temp.loc[index, 'Ilma_Lämpötila_7d_C'] = avg_temp
            df_temp.loc[index, 'Sadanta_7d_mm'] = total_precip
            df_temp.loc[index, 'Tuuli_7d_ms'] = avg_wind_speed
            
            if daily_df is not None:
                # Käytetään DataFrame-indeksiä havainnon ID:nä
                daily_df['Havainto_ID'] = index 
                daily_data_list.append(daily_df)
        
        time.sleep(0.1) # Viive API-kuorman tasaamiseksi
        
    liitetty_lkm = df_temp['Ilma_Lämpötila_7d_C'].count()
    print(f"\nSäämuuttujat liitetty {liitetty_lkm}/{len(df_temp)} havaintoon.")
    
    df_daily_temps = pd.concat(daily_data_list, ignore_index=True) if daily_data_list else pd.DataFrame()
    
    return df_temp, df_daily_temps


# ************************************************
# PÄÄOHJELMA
# ************************************************

if __name__ == "__main__":

    load_dotenv()
    
    # 1. TARKISTA, ONKO RIKASTETTU DATA JO TALLENNETTU
    if os.path.exists(OUTPUT_FILE) and not USE_PARQUET:
        print("="*60)
        print(f"Ladataan rikastettu data tiedostosta: {os.path.basename(OUTPUT_FILE)}")
        print("="*60)
        try:
             df_rikastettu = pd.read_csv(OUTPUT_FILE, sep=';')
             if 'Päivämäärä' in df_rikastettu.columns:
                 df_rikastettu['Päivämäärä'] = pd.to_datetime(df_rikastettu['Päivämäärä'], errors='coerce')
        except Exception as e:
            print(f"Virhe rikastetun datan lukemisessa: {e}. Ajetaan datan luku alusta.")
            df_rikastettu = None
    
    if 'df_rikastettu' not in locals() or df_rikastettu is None or df_rikastettu.empty:
        print("="*60)
        print("Ajetaan datan luku ja rikastus alusta (KÄYTETÄÄN KAIKKEA DATA!).")
        print("="*60)

        # KAIKKI 5 TIEDOSTOA LUETAAN JA YHDISTETÄÄN
        df_raaka = lue_ja_yhdistä_data(file_path)
        if df_raaka is None: exit()
        
        df_ennuste_valmis = puhdista_ja_muunna_data(df_raaka)
        
        if df_ennuste_valmis is None or df_ennuste_valmis.empty:
            print("\nVIRHE: Dataa ei voitu yhdistää ja puhdistaa ennustemalleja varten.")
            exit()
            
        # 2. HAE JA LIITÄ OPEN-METEO LÄMPÖTILA
        # HUOM: Rajoitus .head(100) on POISTETTU! Käytetään koko dataa.
        df_testi_osa = df_ennuste_valmis.copy() 
        
        # Funktio palauttaa kaksi DataFramea: rikastetun ja päivittäisen datan
        df_rikastettu, df_daily_temps = liita_openmeteo_lampotilat(df_testi_osa)
        
        # 3. TALLENNA DATA
        try:
            df_rikastettu.to_csv(OUTPUT_FILE, index=False, sep=';')
            df_daily_temps.to_csv(os.path.join(file_path, 'daily_temperatures_debug.csv'), index=False, sep=';')
                
            print(f"\n=> RIKASTETTU DATA TALLENNETTU ONNISTUNEESTI osoitteeseen: {os.path.basename(OUTPUT_FILE)}")
            print(f"=> Päivittäinen debug-data tallennettu tiedostoon daily_temperatures_debug.csv")
        except Exception as e:
            print(f"\nVIRHE DATAN TALLENTAMISESSA: {e}")

    # --- LOPULLINEN TULOS ---
    print("\n" + "="*50)
    print("LOPULLINEN RIKASTETTU DATA VALMIS ENNUSTUKSEEN")
    print("="*50)
    
    if 'df_rikastettu' in locals() and not df_rikastettu.empty:
        print("Ensimmäiset 10 riviä (7 päivän keskiarvo):")
        print(df_rikastettu[['Päivämäärä', 'Latitude_DD', 'LevätilanneNum', 'Ilma_Lämpötila_7d_C', 'Sadanta_7d_mm', 'Tuuli_7d_ms']].head(10))
        
        if 'Ilma_Lämpötila_7d_C' in df_rikastettu.columns:
            print(f"\nKaikki havainnot yhteensä: {len(df_rikastettu)}")
            print(f"Havaintoja, joissa säädata on: {df_rikastettu['Ilma_Lämpötila_7d_C'].count()}/{len(df_rikastettu)}")
    else:
        print("Valitettavasti DataFramea ei ole luotu tai se on tyhjä.")
    print("="*50)