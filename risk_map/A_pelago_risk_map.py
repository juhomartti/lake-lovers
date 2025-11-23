import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import requests
import datetime
import altair as alt
import re
import os
from PIL import Image

# --- ASETUKSET ---
st.set_page_config(page_title="Riskialueet 2026", layout="wide", page_icon="💧")
MAP_FILE = "fosforikartta.jpg"

# --- CUSTOM CSS (ULKOASU) ---
st.markdown("""
<style>
    /* 1. FONTTI (Inter) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

    /* 2. YLEISET TEKSTIASETUKSET */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #1F2937;
    }

    /* 3. TAUSTAVÄRIT (Beige) */
    .stApp {
        background-color: #F5F5DC !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #35C0B1 !important; /* Hieman tummempi turkoosi sivupalkkiin */
        border-right: 1px solid rgba(255,255,255,0.3);
    }
    
    [data-testid="stHeader"] {
        background-color: transparent !important;
    }

    /* 4. VALKOISET LAATIKOT (KORTIT) - PRO-FIX */
    /* Tämä pakottaa reunustetun laatikon valkoiseksi */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        border: 2px solid #0e4d92;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Pakotetaan kaikki laatikon sisällä oleva valkoiselle pohjalle */
    [data-testid="stVerticalBlockBorderWrapper"] > div {
        background-color: #FFFFFF !important;
    }
    
    /* 5. TYPOGRAFIA */
    h1, h2, h3 {
        color: #003366 !important;
        font-weight: 700;
    }
    
    /* Metriikat */
    div[data-testid="stMetric"] {
        background-color: #F8FAFC !important;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #003366;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Expanderit */
    .streamlit-expanderHeader {
        background-color: #FFFFFF !important;
        color: #003366 !important;
        font-weight: 600;
    }
    .streamlit-expanderContent {
        background-color: #FFFFFF !important;
        color: #1F2937 !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# OSA 1: DATAN LATAUS JA YHDISTÄMINEN
# ---------------------------------------------------------

def siivoa_koordinaatti(coord_str):
    if not isinstance(coord_str, str): return None
    match = re.search(r"(\d+)[\°\s]+(\d+)[\'\s]+([\d\.]+)[\"\s]*([NnSsEeWw]?)", coord_str.replace('"', ''))
    if match:
        deg, minutes, seconds, direction = match.groups()
        val = float(deg) + (float(minutes) / 60) + (float(seconds) / 3600)
        if direction and direction.upper() in ('S', 'W'): val *= -1
        return val
    return None

def hae_vari(riskiluku):
    """ Värisäännöt """
    if riskiluku >= 12: return '#8B0000'  # Tummanpunainen
    if riskiluku >= 8:  return 'red'      # Punainen
    if riskiluku >= 4:  return 'orange'   # Oranssi
    return "#FCFC07"                      # Keltainen

@st.cache_data
def load_and_combine_years():
    all_dfs = []
    years = range(21, 26) # 2021-2025
    
    for i in years:
        # Yritetään löytää tiedosto (pieni tai iso alkukirjain)
        fname = f"havainto{i}.csv" 
        if not os.path.exists(fname):
             fname = f"Havainto{i}.csv" 
             
        if os.path.exists(fname):
            try:
                try: temp_df = pd.read_csv(fname, sep=';', encoding='utf-8')
                except: temp_df = pd.read_csv(fname, sep=';', encoding='iso-8859-1')
                
                temp_df['Vuosi'] = 2000 + i
                all_dfs.append(temp_df)
            except Exception as e:
                pass 
    
    if not all_dfs: return None, None

    df = pd.concat(all_dfs, ignore_index=True)

    if 'Koordinaatit' in df.columns:
        df['Koordinaatit'] = df['Koordinaatit'].astype(str)
        split = df['Koordinaatit'].str.split(',', expand=True)
        if split.shape[1] >= 2:
            df['lat'] = split[0].apply(siivoa_koordinaatti)
            df['lon'] = split[1].apply(siivoa_koordinaatti)
    
    if 'Päivämäärä' in df.columns:
        df['Päivämäärä'] = pd.to_datetime(df['Päivämäärä'], errors='coerce')
        mask = df['Päivämäärä'].notnull()
        df.loc[mask, 'Vuosi'] = df.loc[mask, 'Päivämäärä'].dt.year

    df = df.dropna(subset=['lat', 'lon'])

    df_yearly_max = df.groupby(['Havaintopaikka', 'lat', 'lon', 'Vuosi'])['LevätilanneNum'].max().reset_index()
    
    pivot = df_yearly_max.pivot_table(
        index=['Havaintopaikka', 'lat', 'lon'],
        columns='Vuosi',
        values='LevätilanneNum',
        aggfunc='max'
    ).fillna(0)
    
    pivot['Riskiluku'] = pivot.sum(axis=1)
    pivot['Levävuodet_LKM'] = (pivot > 0).sum(axis=1) - 1 
    pivot['Max_2025'] = pivot.get(2025, 0)
    
    result_df = pivot.reset_index()
    filtteri = (result_df['Riskiluku'] >= 4) | (result_df[list(range(2021, 2026))].max(axis=1) >= 3)
    hotspots = result_df[filtteri].copy()
    
    return hotspots, df

# ---------------------------------------------------------
# OSA 2: SÄÄANALYYSI
# ---------------------------------------------------------

def get_weather_data(lat, lon, date):
    try:
        end = date + datetime.timedelta(days=5)
        start = date - datetime.timedelta(days=30)
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": lat, "longitude": lon,
            "start_date": start.strftime("%Y-%m-%d"),
            "end_date": end.strftime("%Y-%m-%d"),
            "daily": ["temperature_2m_max"], "timezone": "Europe/Helsinki"
        }
        return requests.get(url, params=params).json()
    except: return None

def simulate_water(air):
    water = []
    if len(air) > 0: c = air[0] - 4.0 
    else: c = 5.0
    for t in air:
        c = (c * 0.9) + ((t-3.5) * 0.1)
        water.append(c)
    return water

# ---------------------------------------------------------
# OSA 3: KÄYTTÖLIITTYMÄ
# ---------------------------------------------------------

# HEADER
c_head1, c_head2 = st.columns([3, 1])
with c_head1:
    st.title("Risk of algae 2026") 
    st.markdown("**Multiyear algae problems** | Data: 2021–2025")

with c_head2:
    st.markdown("") 

st.divider()

df_hotspots, df_raw = load_and_combine_years()
try: p_map = Image.open(MAP_FILE)
except: p_map = None

if df_hotspots is None:
    st.error("⚠️ CSV-tiedostoja ei löytynyt. Varmista, että kansiossa on 'havainto21.csv' - 'havainto25.csv'.")
    st.stop()

col_map, col_analysis = st.columns([2, 1.2], gap="large")

# === VASEN: KARTTA (Valkoinen laatikko) ===
with col_map:
    with st.container(border=True):
        st.subheader("Observation Map")
        st.caption("Color indicates the frequency of the problem (Red = recurring)")
        
        m = folium.Map(location=[65, 26], zoom_start=5, tiles="Cartodb Positron")
        marker_cluster = MarkerCluster().add_to(m)
        
        for _, row in df_hotspots.iterrows():
            riski = int(row['Riskiluku'])
            vuodet = int(row['Levävuodet_LKM'])
            max25 = int(row.get('Max_2025', 0))
            
            popup_html = f"""
            <div style="font-family: 'Inter', sans-serif; min-width: 180px; color: #1F2937;">
                <h4 style="margin:0 0 8px 0; color:#0e4d92; font-size: 16px;">{row['Havaintopaikka']}</h4>
                <div style="background-color: #f3f4f6; padding: 8px; border-radius: 6px; font-size: 13px;">
                    <b>Riskiluku:</b> {riski}<br>
                    <b>Vuoden 2025 max:</b> {max25}<br>
                    <b>Ongelmavuosia:</b> {vuodet}/5
                </div>
            </div>
            """
            
            color = hae_vari(riski)
            
            folium.CircleMarker(
                location=[row['lat'], row['lon']],
                radius=9,
                color=color, fill=True, fill_color=color, fill_opacity=0.8,
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{row['Havaintopaikka']} ({vuodet}/5v)"
            ).add_to(marker_cluster)
            
        st_map = st_folium(m, width=None, height=700)

# === OIKEA: ANALYYSI (Valkoinen laatikko) ===
with col_analysis:
    if not (st_map and st_map['last_object_clicked']):
        with st.container(border=True):
            st.info("👈 **Start analysis by clicking a dot on the map.**")
            st.markdown("Select a location to see:")
            st.markdown("- Recurrence history")
            st.markdown("- Weather analysis at bloom time")
            
            if p_map: 
                st.image(p_map, caption="Phosphorus load (Reference)", width="stretch")
    
    else:
        lat = st_map['last_object_clicked']['lat']
        lon = st_map['last_object_clicked']['lng']
        
        df_hotspots['dist'] = ((df_hotspots['lat']-lat)**2 + (df_hotspots['lon']-lon)**2)
        match = df_hotspots.loc[df_hotspots['dist'].idxmin()]
        paikka = match['Havaintopaikka']
        
        # --- KOHDEKORTTI ---
        with st.container(border=True):
            st.subheader(f"{paikka}")
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Risk number", int(match['Riskiluku']))
            m2.metric("Problem years", f"{int(match['Levävuodet_LKM'])} / 5")
            m3.metric("Max 2025", int(match.get('Max_2025', 0)))
            
            havainnot = df_raw[df_raw['Havaintopaikka'] == paikka].sort_values('Päivämäärä', ascending=False)
            
            st.markdown("### 📅 Observation History")
            opts = {f"{r['Päivämäärä'].strftime('%d.%m.%Y')} (Level {r['LevätilanneNum']})": r['Päivämäärä'] for _, r in havainnot.iterrows()}
            valinta = st.selectbox("Select observation to view:", list(opts.keys()))
            
            if valinta:
                pvm = opts[valinta].date()
                
                st.markdown("Water temperature")
                with st.spinner("Analyzing weather data..."):
                    w = get_weather_data(lat, lon, pvm)
                    
                if w:
                    dates = pd.to_datetime(w['daily']['time'])
                    air = w['daily']['temperature_2m_max']
                    water = simulate_water(air)
                    
                    df_c = pd.DataFrame({"Pvm": dates, "Vesi": water, "Ilma": air})
                    
                    base = alt.Chart(df_c).encode(x=alt.X('Pvm', axis=alt.Axis(format='%d.%m'), title="Päivämäärä"))
                    
                    line = base.mark_line(color='#0e4d92', strokeWidth=3).encode(
                        y=alt.Y('Vesi', title='Lämpötila °C'),
                        tooltip=['Pvm', 'Vesi', 'Ilma']
                    )
                    
                    line_air = base.mark_line(color='#f59e0b', strokeDash=[5,5], opacity=0.7).encode(y='Ilma')
                    
                    rule = alt.Chart(pd.DataFrame({'d': [pd.to_datetime(pvm)]})).mark_rule(color='#dc2626', strokeWidth=2).encode(x='d')
                    
                    st.altair_chart((line + line_air + rule).interactive(), width="stretch")
                    
                    max_w = df_c[df_c['Pvm'] <= pd.to_datetime(pvm)]['Vesi'].max()
                    
                    if max_w > 19: 
                        st.error(f"**NOTE** Water was unusually warm ({max_w:.1f}°C).")
                    else: 
                        st.info(f"**Nutrients:** Water was cool ({max_w:.1f}°C). Bloom is likely due to nutrients.")
        
        if p_map:
            with st.expander("Show nutrient load (Phosphorus)"):
                st.image(p_map, width="stretch")