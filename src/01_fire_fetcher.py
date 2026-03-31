
# FIREWATCH AI — Fáze 1: Sběr meteorologických dat
 
# Co tento skript dělá:
#   1. Projde mapovou síť (grid) České republiky bod po bodu
#   2. Pro každý bod stáhne historická data z bezplatného Open-Meteo API
#   3. Každý den ohodnotí — je v ten den kritické riziko požáru? (1 = ANO, 0 = NE)
#   4. Výsledek uloží do CSV souboru pro další zpracování (trénování modelu)

 

import requests          
import pandas as pd      
import time              
import os                


# SEKCE 1: NASTAVENÍ PROJEKTU (konstanty)



DATUM_START = "2022-01-01"
DATUM_KONEC = "2023-12-31"

# Bounding box = obdélník ohraničující celé území ČR
LAT_MIN  = 48.6   
LAT_MAX  = 51.0   
LON_MIN  = 12.1   
LON_MAX  = 18.8   
KROK     = 0.5   

# --- Fyzikální prahy pro rozhodnutí: RIZIKO POŽÁRU = 1 ---
PRAH_TEPLOTA    = 28.0   
PRAH_SRAZKY     = 0.0    
PRAH_VITR       = 15.0   
PRAH_SLUNCE     = 20.0   

# Vyvažování datasetu
KAZDÝ_NTY_BEZPECNY = 20  

VÝSTUPNÍ_SLOŽKA = os.path.join("data", "raw")
VÝSTUPNÍ_SOUBOR = os.path.join(VÝSTUPNÍ_SLOŽKA, "fire_raw.csv")

# SEKCE 2: PŘÍPRAVA PROSTŘEDÍ

if not os.path.exists(VÝSTUPNÍ_SLOŽKA):
    os.makedirs(VÝSTUPNÍ_SLOŽKA, exist_ok=True)
    print(f"[INFO] Vytvořena složka: {VÝSTUPNÍ_SLOŽKA}")

# SEKCE 3: DEFINICE FUNKCE PRO VOLÁNÍ API

def stahni_data_pro_bod(lat, lon, datum_start, datum_konec):
    """Stáhne meteorologická data pro jeden zeměpisný bod."""
    url = "https://archive-api.open-meteo.com/v1/archive"

    parametry = {
        "latitude":   lat,
        "longitude":  lon,
        "start_date": datum_start,
        "end_date":   datum_konec,
        "daily": ",".join([
            "temperature_2m_max",
            "precipitation_sum",
            "wind_speed_10m_max",
            "shortwave_radiation_sum",
        ]),
        "timezone": "Europe/Prague",
    }

    try:
        odpoved = requests.get(url, params=parametry, timeout=30)
        if odpoved.status_code != 200:
            return None
        return odpoved.json()
    except:
        return None

# SEKCE 4: HLAVNÍ LOGIKA — průchod gridem


vsechny_zaznamy = []
pocet_bodu_celkem    = 0
pocet_bodu_uspesnych = 0
pocet_riziko_dni     = 0
pocet_bezpecnych_dni = 0

print("   FIREWATCH AI — Spouštím stahování dat")

lat_aktualni = LAT_MIN
while lat_aktualni <= LAT_MAX:
    lon_aktualni = LON_MIN
    while lon_aktualni <= LON_MAX:

        lat = round(lat_aktualni, 1)
        lon = round(lon_aktualni, 1)

        pocet_bodu_celkem += 1
        print(f"\n[BOD {pocet_bodu_celkem}] Stahuji: lat={lat}, lon={lon} ...")

        raw_data = stahni_data_pro_bod(lat, lon, DATUM_START, DATUM_KONEC)

        if raw_data is None or "daily" not in raw_data:
            print(f"  -> Přeskočen (chyba nebo chybí data)")
            lon_aktualni = round(lon_aktualni + KROK, 1)
            continue

        nadmorska_vyska = raw_data.get("elevation", 0.0)
        denni_data = raw_data["daily"]

        seznam_dat     = denni_data["time"]
        seznam_teplota = denni_data["temperature_2m_max"]
        seznam_srazky  = denni_data["precipitation_sum"]
        seznam_vitr    = denni_data["wind_speed_10m_max"]
        seznam_slunce  = denni_data["shortwave_radiation_sum"]

        pocitadlo_bezpecnych = 0

        for i in range(len(seznam_dat)):
            datum   = seznam_dat[i]
            teplota = seznam_teplota[i]
            srazky  = seznam_srazky[i]
            vitr    = seznam_vitr[i]
            slunce  = seznam_slunce[i]

            # Ošetření prázdných hodnot
            if teplota is None or srazky is None or vitr is None or slunce is None:
                continue

            # LOGIKA: Je to rizikový den?
            je_horko  = teplota > PRAH_TEPLOTA
            je_sucho  = srazky <= PRAH_SRAZKY
            je_vitr   = vitr > PRAH_VITR
            je_slunce = slunce > PRAH_SLUNCE

            if je_horko and je_sucho and je_vitr and je_slunce:
                riziko = 1
                pocet_riziko_dni += 1
            else:
                riziko = 0

            # Podvzorkování bezpečných dnů
            if riziko == 0:
                pocitadlo_bezpecnych += 1
                if pocitadlo_bezpecnych % KAZDÝ_NTY_BEZPECNY != 0:
                    continue
                pocet_bezpecnych_dni += 1

            zaznam = {
                "datum":             datum,
                "lat":               lat,
                "lon":               lon,
                "nadmorska_vyska_m": nadmorska_vyska,
                "teplota_max_C":     teplota,
                "srazky_mm":         srazky,
                "vitr_max_kmh":      vitr,
                "slunce_MJm2":       slunce,
                "riziko_pozaru":     riziko,
            }
            vsechny_zaznamy.append(zaznam)

        pocet_bodu_uspesnych += 1
        print(f"  -> OK | výška: {nadmorska_vyska:.0f} m | dní zpracováno: {len(seznam_dat)}")

        time.sleep(0.5)
        lon_aktualni = round(lon_aktualni + KROK, 1)

    lat_aktualni = round(lat_aktualni + KROK, 1)

# SEKCE 5: ULOŽENÍ VÝSLEDKŮ DO CSV SOUBORU

print("\n" + "=" * 60)
print("   Průchod gridem dokončen. Ukládám výsledky...")
print("=" * 60)

if len(vsechny_zaznamy) == 0:
    print("[CHYBA] Nebyla stažena žádná data!")
else:
    df = pd.DataFrame(vsechny_zaznamy)
    df = df.sort_values(by="datum").reset_index(drop=True)
    df.to_csv(VÝSTUPNÍ_SOUBOR, index=False, encoding="utf-8-sig")

    print(f"\n[HOTOVO] Výsledky uloženy do: {VÝSTUPNÍ_SOUBOR}")
    print(f"\n--- Statistika datasetu ---")
    print(f"  Zpracovaných bodů gridu:   {pocet_bodu_uspesnych} / {pocet_bodu_celkem}")
    print(f"  Celkem řádků (dní) v CSV:  {len(df)}")
    print(f"  Z toho RIZIKOVÝCH dní:     {pocet_riziko_dni}  (riziko = 1)")
    print(f"  Z toho BEZPEČNÝCH dní:     {pocet_bezpecnych_dni}  (riziko = 0)")
    
    if len(df) > 0:
        print(f"  Poměr rizikových:          {pocet_riziko_dni / len(df) * 100:.1f} %")