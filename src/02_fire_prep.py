# FIREWATCH AI — Fáze 2: Příprava, čištění a škálování dat
# Co skript dělá: Vyčistí surová data, odstraní textový sloupec "datum" 
# a naškáluje fyzikální veličiny do rozmezí 0-1 pomocí MinMaxScaleru.

import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import os

print("=" * 60)
print("   FIREWATCH AI — Fáze 2: Příprava a čištění dat")
print("=" * 60)

# 1. NAČTENÍ DAT
vstupni_soubor = os.path.join("data", "raw", "fire_raw.csv")

if not os.path.exists(vstupni_soubor):
    print(f"[CHYBA] Soubor {vstupni_soubor} neexistuje! Spusť nejdřív fetcher.")
    exit()

df = pd.read_csv(vstupni_soubor)
print(f" Načteno záznamů: {len(df)}")

# 2. ČIŠTĚNÍ DAT
df = df.dropna()

if "datum" in df.columns:
    df = df.drop(columns=["datum"])
    print(" Odstraněn textový sloupec 'datum' (model potřebuje jen čísla).")

# 3. ŠKÁLOVÁNÍ DAT (MinMaxScaler)

sloupce_ke_skalovani = [
    "lat", "lon", "nadmorska_vyska_m", 
    "teplota_max_C", "srazky_mm", 
    "vitr_max_kmh", "slunce_MJm2"
]

print("\n--- Ukázka PŘED škálováním (reálné hodnoty) ---")
print(df[sloupce_ke_skalovani].head(3).to_string())

# Inicializace škálovače
skalovac = MinMaxScaler()

# Aplikujeme škálování na vybrané sloupce 
df[sloupce_ke_skalovani] = skalovac.fit_transform(df[sloupce_ke_skalovani])

print("\n--- Ukázka PO škálování ---")
print(df[sloupce_ke_skalovani].head(3).to_string())

# 4. ULOŽENÍ HOTOVÝCH DAT
vystupni_slozka = os.path.join("data", "processed")
os.makedirs(vystupni_slozka, exist_ok=True)
vystupni_soubor = os.path.join(vystupni_slozka, "fire_processed.csv")

df.to_csv(vystupni_soubor, index=False)

print(f" Hotovo! Vyčištěná data uložena do: {vystupni_soubor}")
