
# 🔥 FireWatch AI

| | |
|---|---|
| **Autor** | Alexandre Basseville |
| **Rok** | 2026 |
| **Technologie** | Python, Streamlit, Folium, Scikit-Learn, Altair, Open-Meteo API |

## O projektu

FireWatch AI je pokročilý expertní systém navržený pro predikci a analýzu rizika lesních požárů na území České republiky. Projekt nevyužívá jen prosté statistiky, ale kombinuje orografická data (nadmořská výška, GPS) s aktuálními fyzikálními parametry atmosféry.

Celý systém je postaven na modelu Deep Learning (neuronová síť), který byl natrénován na historických datech extrémních požárních událostí. Výsledkem je interaktivní velitelský panel, který slouží pro krizové řízení a preventivní ochranu lesních porostů.

## Hlavní funkce

- 🗺️ **Interaktivní mapa (Folium):** Umožňuje záchranářům vybrat jakoukoliv lokalitu v ČR pouhým kliknutím.
- 🔍 **Geocoding:** Vyhledávání oblastí podle názvu (např. *Hřensko* nebo *Šumava*) pomocí integrovaného API.
- 🤖 **AI Risk Engine:** Výpočet procentuální pravděpodobnosti rizika pomocí neuronové sítě (MLPClassifier).
- 📊 **Explainable AI (XAI):** Vizualizace vlivu jednotlivých faktorů (vítr, teplota, sucho) na konkrétní rozhodnutí modelu.
- 🧪 **Simulační režim (What-If):** Nástroj pro krizové štáby umožňující simulovat extrémní podmínky a sledovat odezvu modelu.
- 🌊 **Fyzikální model šíření:** Odhad rychlosti šíření ohně a výpočet evakuačního perimetru.
- 📄 **Export hlášení:** Automatické generování operačních hlášení pro jednotky IZS.

## Instalace a spuštění

**1. Klonování repozitáře:**

```bash
git clone <url-vašeho-repozitáře>
cd FireWatch
```

**2. Instalace potřebných knihoven:**

```bash
pip install pandas scikit-learn requests streamlit folium streamlit-folium altair joblib
```

**3. Spuštění webové aplikace:**

```bash
python -m streamlit run src/04_app.py
```

## Architektura projektu

Projekt je logicky rozdělen do čtyř fází, které na sebe navazují:

| Soubor | Popis |
|---|---|
| `src/01_fire_fetcher.py` | Automatizovaný sběr geografických a meteorologických dat (Grid Sampling) |
| `src/02_data_prep.py` | Čištění, filtrace a normalizace dat pomocí MinMaxScaler |
| `src/03_train_colab.py` | Architektura neuronové sítě, trénink, křížová validace a extrakce XAI parametrů |
| `src/04_app.py` | Finální webové rozhraní v prostředí Streamlit |