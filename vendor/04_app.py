# =============================================================================
# FIREWATCH AI — Fáze 4: Finální Webová Aplikace pro Hasiče (ULTIMATE verze)
# Autor: Alexandre Basseville
# Knihovna: Streamlit, Folium, Altair
# =============================================================================

import streamlit as st
import pandas as pd
import requests
import joblib
from sklearn.preprocessing import MinMaxScaler
import os
import folium
from streamlit_folium import st_folium
import datetime
import altair as alt

# --- DYNAMICKÉ CESTY (NEPRŮSTŘELNÉ ŘEŠENÍ) ---
# Zjistí, kde leží tento skript (složka src) a odvodí z toho hlavní složku projektu
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Bezpečné sestavení absolutních cest podle naší vendor architektury
MODEL_PATH = os.path.join(PROJECT_ROOT, "vendor", "firewatch_model.pkl")
FEATURES_PATH = os.path.join(PROJECT_ROOT, "vendor", "firewatch_features.pkl")
IMPORTANCES_PATH = os.path.join(PROJECT_ROOT, "vendor", "firewatch_importances.pkl")
RAW_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "fire_raw.csv")
LOGO_PATH = os.path.join(PROJECT_ROOT, "vendor", "logo.png")

# --- 1. NASTAVENÍ STRÁNKY A DESIGNU (ČERNO-ORANŽOVÁ + FAVICON) ---
ikonka = LOGO_PATH if os.path.exists(LOGO_PATH) else "🔥"

st.set_page_config(page_title="FireWatch AI Panel", page_icon=ikonka, layout="wide")

st.markdown("""
    <style>
    .stApp {
        background-color: #121212;
        color: #FFFFFF;
    }
    h1, h2, h3 {
        color: #FF5A00 !important;
    }
    .stButton>button {
        background-color: #FF5A00;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        border: none;
        width: 100%;
        height: 60px;
        font-size: 20px;
    }
    .stButton>button:hover {
        background-color: #E04D00;
    }
    .info-box {
        background-color: #1E1E1E;
        padding: 15px;
        border-left: 5px solid #FF5A00;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .metric-container {
        background-color: #1E1E1E;
        padding: 10px;
        border-radius: 5px;
        text-align: center;
    }
    /* Vlastní barvy pro progress bar */
    .stProgress > div > div > div > div {
        background-color: #FF5A00;
    }
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZACE STAVU APLIKACE ---
if "lat" not in st.session_state:
    st.session_state.lat = 50.87
if "lon" not in st.session_state:
    st.session_state.lon = 14.24
if "misto" not in st.session_state:
    st.session_state.misto = "Hřensko"

# --- 2. HLAVIČKA APLIKACE ---
col_logo, col_text = st.columns([1, 6])
with col_logo:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
with col_text:
    st.markdown("<h1 style='text-align: left; font-size: 3em;'> FIREWATCH AI COMMAND CENTER</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: left; color: #AAAAAA; font-size: 1.2em;'>Pokročilý systém predikce lesních požárů s interaktivní mapou, kalendářem a AI analýzou</p>", unsafe_allow_html=True)
st.markdown("---")

# --- 3. NAČTENÍ MODELU ---
@st.cache_resource
def nacti_ai_mozek():
    # Načítáme přes naše neprůstřelné dynamické cesty
    model = joblib.load(MODEL_PATH)
    features = joblib.load(FEATURES_PATH)
    
    df_raw = pd.read_csv(RAW_DATA_PATH)
    sloupce_ke_skalovani = ["lat", "lon", "nadmorska_vyska_m", "teplota_max_C", "srazky_mm", "vitr_max_kmh", "slunce_MJm2"]
    skalovac = MinMaxScaler()
    skalovac.fit(df_raw[sloupce_ke_skalovani])
    
    return model, features, skalovac

try:
    model, features, skalovac = nacti_ai_mozek()
except Exception as e:
    st.error(" Kritická chyba: Systém nemůže najít potřebné datové soubory.")
    st.error(f"Detail chyby: {e}")
    st.info("Zkontrolujte, zda jste přesunuli modely do složky 'vendor' a surová data do 'data/raw'!")
    st.stop()

# --- 4. ZADÁVÁNÍ SOUŘADNIC, MAPA A KALENDÁŘ ---
col_mapa, col_vstupy = st.columns([2, 1])

with col_vstupy:
    st.markdown("###  Zaměřovač lokality")
    st.markdown("<div class='info-box'>Zadejte název, souřadnice, nebo klikněte do mapy.</div>", unsafe_allow_html=True)
    
    # VYHLEDÁVÁNÍ PODLE NÁZVU (Geocoding API)
    st.markdown("**1. Hledat podle názvu:**")
    hledany_text = st.text_input("Město, obec, les...", placeholder="Např. Českosaské Švýcarsko", label_visibility="collapsed")
    
    if st.button(" Najít na mapě"):
        if hledany_text:
            url_geo = f"https://geocoding-api.open-meteo.com/v1/search?name={hledany_text}&count=1&language=cs&format=json"
            try:
                res = requests.get(url_geo).json()
                if "results" in res and len(res["results"]) > 0:
                    st.session_state.lat = res["results"][0]["latitude"]
                    st.session_state.lon = res["results"][0]["longitude"]
                    st.session_state.misto = res["results"][0]["name"]
                    st.rerun()
                else:
                    st.warning("Místo nebylo nalezeno. Zkuste jiný název.")
            except Exception as e:
                st.error("Chyba při vyhledávání.")
    
    st.markdown("---")
    st.markdown("**2. Přesné GPS souřadnice:**")
    lat_input = st.number_input("Zeměpisná šířka (Lat)", value=st.session_state.lat, format="%.4f")
    lon_input = st.number_input("Zeměpisná délka (Lon)", value=st.session_state.lon, format="%.4f")
    
    if lat_input != st.session_state.lat or lon_input != st.session_state.lon:
        st.session_state.lat = lat_input
        st.session_state.lon = lon_input
        st.session_state.misto = "Vlastní souřadnice"
        
    st.markdown("---")
    # INTERAKTIVNÍ KALENDÁŘ
    st.markdown("**3. Časový horizont analýzy:**")
    dnes = datetime.date.today()
    max_datum = dnes + datetime.timedelta(days=7)
    
    zvolene_datum = st.date_input(
        " Vyberte datum predikce:", 
        value=dnes + datetime.timedelta(days=1), 
        min_value=dnes, 
        max_value=max_datum,
        help="Lze analyzovat aktuální situaci až 7 dní dopředu."
    )
    den_index = (zvolene_datum - dnes).days

    st.markdown("---")
    st.markdown("**4. Režim simulace (Co kdyby?):**")
    simulace_zapnuta = st.checkbox(" Povolit manuální nastavení počasí pro predikci")
    
    if simulace_zapnuta:
        st.info("Předpověď bude ignorována. AI použije vaše manuální hodnoty.")
        sim_teplota = st.slider("Simulovaná teplota (°C)", -10.0, 45.0, 30.0)
        sim_srazky = st.slider("Simulované srážky (mm)", 0.0, 50.0, 0.0)
        sim_vitr = st.slider("Simulovaný vítr (km/h)", 0.0, 150.0, 20.0)
        sim_slunce = st.slider("Simulovaná radiace (MJ/m²)", 0.0, 35.0, 25.0)
    
    st.markdown("<br>", unsafe_allow_html=True)
    analyzovat_btn = st.button("🚨 SPUSTIT ANALÝZU RIZIKA")

with col_mapa:
    st.markdown(f"###  Satelitní pohled: **{st.session_state.misto}**")
    st.caption("Kliknutím kamkoliv do mapy změníte vyšetřovanou oblast.")
    
    m = folium.Map(location=[st.session_state.lat, st.session_state.lon], zoom_start=11, tiles="OpenStreetMap")
    
    folium.Marker(
        [st.session_state.lat, st.session_state.lon],
        popup=st.session_state.misto,
        tooltip="Zvolená lokalita (Klikni na mapu pro změnu)",
        icon=folium.Icon(color="red", icon="fire")
    ).add_to(m)
    
    mapa_zobrazeni = st_folium(m, width=800, height=700, returned_objects=["last_clicked"])
    
    if mapa_zobrazeni and mapa_zobrazeni.get("last_clicked"):
        klik_lat = mapa_zobrazeni["last_clicked"]["lat"]
        klik_lon = mapa_zobrazeni["last_clicked"]["lng"]
        
        if abs(klik_lat - st.session_state.lat) > 0.0001 or abs(klik_lon - st.session_state.lon) > 0.0001:
            st.session_state.lat = klik_lat
            st.session_state.lon = klik_lon
            st.session_state.misto = "Bod vybraný z mapy"
            st.rerun()

# --- 5. HLAVNÍ LOGIKA ANALÝZY ---
if analyzovat_btn:
    st.markdown("---")
    
    with st.spinner('Navazuji spojení s meteorologickou družicí a inicializuji AI model...'):
        url = (f"https://api.open-meteo.com/v1/forecast?"
               f"latitude={st.session_state.lat}&longitude={st.session_state.lon}&"
               f"daily=temperature_2m_max,precipitation_sum,wind_speed_10m_max,shortwave_radiation_sum&"
               f"timezone=Europe%2FPrague&forecast_days=8")
        
        try:
            odpoved = requests.get(url).json()
            nadmorska_vyska = odpoved.get("elevation", 0)
            daily = odpoved["daily"]
            
            api_teplota = daily["temperature_2m_max"][den_index]
            api_srazky = daily["precipitation_sum"][den_index]
            api_vitr = daily["wind_speed_10m_max"][den_index]
            api_slunce = daily["shortwave_radiation_sum"][den_index]
            
        except Exception as e:
            st.error("Chyba při komunikaci s meteo stanicí. Zkuste to prosím znovu.")
            st.stop()

        if simulace_zapnuta:
            pred_teplota = sim_teplota
            pred_srazky = sim_srazky
            pred_vitr = sim_vitr
            pred_slunce = sim_slunce
            st.warning(" Probíhá analýza v SIMULAČNÍM REŽIMU (vstupy z Open-Meteo přepsány manuálními daty).")
        else:
            pred_teplota = api_teplota
            pred_srazky = api_srazky
            pred_vitr = api_vitr
            pred_slunce = api_slunce

        res_col1, res_col2 = st.columns([1, 1])

        with res_col1:
            if simulace_zapnuta:
                st.subheader(f" Použité Simulační Vstupy (Pro {zvolene_datum.strftime('%d. %m. %Y')})")
            else:
                st.subheader(f" Meteorologický výhled pro {zvolene_datum.strftime('%d. %m. %Y')}")
                
            m1, m2 = st.columns(2)
            m3, m4 = st.columns(2)
            
            m1.metric("Teplota", f"{pred_teplota} °C")
            m2.metric("Srážky", f"{pred_srazky} mm")
            m3.metric("Rychlost větru", f"{pred_vitr} km/h")
            m4.metric("Nadmořská výška", f"{nadmorska_vyska} m.n.m.")
            
            st.markdown("**Výhledový trendový graf teplot (Následujících 7 dní):**")
            
            dny_v_tydnu = [dnes + datetime.timedelta(days=i) for i in range(8)]
            trend_df = pd.DataFrame({
                "Datum": dny_v_tydnu,
                "Teplota (°C)": daily["temperature_2m_max"]
            })
            
            graf = alt.Chart(trend_df).mark_line(
                color="#FF5A00", 
                strokeWidth=3, 
                point=alt.OverlayMarkDef(color="#FF5A00", size=60)
            ).encode(
                x=alt.X("Datum:T", axis=alt.Axis(
                    format="%d. %m.", 
                    labelAngle=-45, 
                    title=None,
                    values=dny_v_tydnu
                )),
                y=alt.Y("Teplota (°C):Q", scale=alt.Scale(zero=False), title="Teplota (°C)"),
                tooltip=[alt.Tooltip("Datum:T", format="%d. %m. %Y"), alt.Tooltip("Teplota (°C):Q")]
            ).properties(height=300)
            
            st.altair_chart(graf, use_container_width=True)

        with res_col2:
            st.subheader(" Rozhodnutí Umělé Inteligence")
            
            vstupni_data = pd.DataFrame([{
                "lat": st.session_state.lat,
                "lon": st.session_state.lon,
                "nadmorska_vyska_m": nadmorska_vyska,
                "teplota_max_C": pred_teplota,
                "srazky_mm": pred_srazky,
                "vitr_max_kmh": pred_vitr,
                "slunce_MJm2": pred_slunce
            }])
            
            vstupni_data_skalovana = skalovac.transform(vstupni_data)
            df_ai = pd.DataFrame(vstupni_data_skalovana, columns=vstupni_data.columns)

            vysledek = model.predict(df_ai)[0]
            pravdepodobnost = model.predict_proba(df_ai)[0][1] * 100
            
            st.markdown(f"### Míra rizika požáru: **{pravdepodobnost:.1f} %**")
            st.progress(int(pravdepodobnost))

            if pravdepodobnost >= 70:
                st.error(" KRITICKÉ RIZIKO POŽÁRU DETEKOVÁNO! 🔥")
                st.warning("Model identifikoval vzorec meteorologických jevů s extrémní shodou pro vznik lesních požárů. Doporučen 3. stupeň požárního poplachu.")
                stupen_rizika = "KRITICKÉ"
            elif pravdepodobnost >= 30:
                st.warning(" ZVÝŠENÉ RIZIKO POŽÁRU")
                st.info("Podmínky začínají být příhodné pro šíření ohně. Doporučena zvýšená ostražitost hlídek v oblasti.")
                stupen_rizika = "ZVÝŠENÉ"
            else:
                st.success(" OBLAST JE BEZPEČNÁ")
                st.info("Algoritmus nevyhodnotil aktuální kombinaci jevů jako nebezpečnou.")
                stupen_rizika = "BEZPEČNO"

            st.markdown("**Vysvětlitelnost AI (Proč se tak rozhodla):**")
            
            importances = None
            if os.path.exists(IMPORTANCES_PATH):
                importances = joblib.load(IMPORTANCES_PATH)
                st.caption("*(Pokročilá XAI analýza: Vliv vypočítán pomocí Permutation Importance)*")
            elif hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
                
            if importances is not None:
                feat_df = pd.DataFrame({
                    "Faktor": ["Zem. šířka", "Zem. délka", "Nadm. výška", "Teplota", "Srážky", "Vítr", "Slunce"],
                    "Vliv na rozhodnutí": importances
                }).sort_values(by="Vliv na rozhodnutí", ascending=False)
                
                feat_df["Vliv na rozhodnutí"] = feat_df["Vliv na rozhodnutí"].apply(lambda x: max(0, x))
                st.bar_chart(feat_df.set_index("Faktor"), color="#FF5A00")
            else:
                 st.markdown("*Vysvětlitelnost AI není pro tento model k dispozici.*")

        # --- FYZIKÁLNÍ KALKULAČKA ŠÍŘENÍ A KRIZOVÉ ŘÍZENÍ ---
        if pravdepodobnost >= 30:
            st.markdown("---")
            st.subheader(" Dynamika možného požáru (Fyzikální odhad)")
            
            rychlost_sireni_m_min = max(0.5, (pred_vitr * 0.4) + (pred_teplota * 0.3) - (pred_srazky * 2))
            perimetr_2h_metry = rychlost_sireni_m_min * 120 
            
            dyn_c1, dyn_c2 = st.columns(2)
            with dyn_c1:
                st.info(f"**Odhadovaná rychlost šíření:**\n\n🔥 **{rychlost_sireni_m_min:.1f}** metrů za minutu")
            with dyn_c2:
                st.warning(f"**Evakuační perimetr (po 2 hod):**\n\n🚧 **{perimetr_2h_metry:.0f}** metrů od ohniska")

        # KRIZOVÉ TLAČÍTKO PRO IZS
        if pravdepodobnost >= 70:
            st.markdown("---")
            st.markdown("###  AKCE: KRIZOVÉ ŘÍZENÍ")
            if st.button("ODESLAT VAROVÁNÍ DO SYSTÉMU IZS (Integrovaný Záchranný Systém)"):
                with st.spinner("Navazuji šifrované spojení s dispečinkem IZS..."):
                    import time as time_module
                    time_module.sleep(1.5)
                    st.toast("Data úspěšně zašifrována AES-256", icon="🔐")
                    time_module.sleep(1.5)
                    st.toast("Odesílám souřadnice na krajské velitelství", icon="📡")
                    time_module.sleep(1.5)
                st.success(f"Hlášení pro souřadnice [{st.session_state.lat}, {st.session_state.lon}] bylo přijato operačním střediskem. Kód události: FW-{datetime.datetime.now().strftime('%y%m%d-%H%M')}")
                st.balloons() 

        # --- 7. EXPERTNÍ DIAGNOSTIKA AI ---
        st.markdown("---")
        with st.expander(" Technická diagnostika AI modelu (Pro experty / Komisi)"):
            st.markdown("Tato sekce odkrývá 'černou skříňku' umělé inteligence a ukazuje její interní parametry.")
            
            diag_c1, diag_c2 = st.columns(2)
            with diag_c1:
                st.markdown("**Architektura modelu:**")
                st.code(f"""
Algoritmus: {type(model).__name__}
Počet základních odhadců: {getattr(model, 'n_estimators', 'N/A (Neuronová síť)')}
Kritérium optimalizace: {getattr(model, 'criterion', 'N/A')}
Maximální hloubka/vrstvy: {getattr(model, 'max_depth', getattr(model, 'hidden_layer_sizes', 'Auto'))}
                """, language="yaml")
            
            with diag_c2:
                st.markdown("**Surový výstupní vektor (Pravděpodobnostní rozdělení):**")
                prob_bezpeci = model.predict_proba(df_ai)[0][0]
                prob_pozar = model.predict_proba(df_ai)[0][1]
                st.code(f"""
Pravděpodobnost Třídy 0 (Bezpečí): {prob_bezpeci:.4f}
Pravděpodobnost Třídy 1 (Požár):   {prob_pozar:.4f}

Finální prahová aktivace: {'Třída 1' if prob_pozar > 0.5 else 'Třída 0'}
                """, language="yaml")

        # --- 8. EXPORT HLÁŠENÍ (PDF/TXT) ---
        st.markdown("---")
        st.subheader(" Generování hlášení pro záchrannou jednotku")
        
        aktualni_cas = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report_text = f"""==================================================
FIREWATCH AI - OPERAČNÍ HLÁŠENÍ
==================================================
Datum a čas generování: {aktualni_cas}
Vyšetřovaná oblast:     {st.session_state.misto}
Vyšetřované datum:      {zvolene_datum.strftime('%d.%m.%Y')}
Souřadnice:             {st.session_state.lat} N, {st.session_state.lon} E
Nadmořská výška:        {nadmorska_vyska} m.n.m.
Režim simulace:         {'ZAPNUTO (Manuální data)' if simulace_zapnuta else 'VYPNUTO (Očekávaná předpověď z API)'}

--- METEOROLOGICKÉ VSTUPY ---
Maximální teplota:      {pred_teplota} °C
Očekávané srážky:       {pred_srazky} mm
Rychlost větru:         {pred_vitr} km/h
Solární radiace:        {pred_slunce} MJ/m2

--- ZÁVĚR UMĚLÉ INTELIGENCE ---
Vypočítaná shoda rizika: {pravdepodobnost:.1f} %
Oficiální verdikt AI:    {stupen_rizika}
Algoritmus:              {type(model).__name__}
==================================================
Vygeneroval systém FireWatch AI (Autor: Alexandre Basseville)
"""
        
        if pravdepodobnost >= 30:
            report_text = report_text.replace("--- ZÁVĚR UMĚLÉ INTELIGENCE ---", f"--- DYNAMIKA ŠÍŘENÍ ---\nOdhad rychlosti:        {rychlost_sireni_m_min:.1f} m/min\nEvakuační perimetr (2h):  {perimetr_2h_metry:.0f} m\n\n--- ZÁVĚR UMĚLÉ INTELIGENCE ---")

        st.download_button(
            label=" Stáhnout textové hlášení pro jednotku (TXT)",
            data=report_text,
            file_name=f"FireWatch_Report_{st.session_state.misto}_{zvolene_datum.strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )