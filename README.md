# 💪 Physio & Sports Command Center

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.46+-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Plotly](https://img.shields.io/badge/Plotly-5.18+-3F4F75?logo=plotly&logoColor=white)](https://plotly.com/)
[![Ollama](https://img.shields.io/badge/AI-Ollama%20%7C%20Local-black?logo=ollama&logoColor=white)](https://ollama.com/)

**Universal Adaptive Biomechanical & Sports Analytics Platform powered by Local AI.**

Uniwersalna platforma do analizy danych biomechanicznych, testów sprawnościowych i parametrów fizjoterapeutycznych z adaptacyjnym dashboardem wizualizacyjnym oraz lokalnym modelem AI (Ollama).

---

## 🌟 Główne Funkcje / Key Features

### 1. 🎯 Uniwersalna Autoadaptacja do Dowolnych Danych (Universal Schema Profiling)
Platforma nie wymaga sztywnej struktury kolumn. Po wrzuceniu pliku `.xlsx` lub `.csv` do katalogu `inbox/` system automatycznie:
- Rozpoznaje typ badania (np. **Eurofit**, dynamometria izokinetyczna **Biodex**, platformy sił / CMJ, tracking GPS, badania wydolnościowe).
- Wykrywa identyfikatory zawodników/pacjentów, kolumny kategoryczne (grupy, pozycje, dyscypliny, płeć) oraz wskaźniki ilościowe.
- Dynamicznie generuje dopasowany zestaw wykresów i statystyk.

### 2. 📊 Zaawansowany Zestaw Wizualizacji (Advanced Visual Suite)
- **🕸️ Radar Wielowymiarowy (Multi-Metric Percentile Spider Chart)**: Profilowanie zawodnika na tle mediany grupy oraz średniej dyscypliny (skala percentylowa 0–100%).
- **🏆 Rankingi i Liderzy**: Automatyczne zestawienie najlepszych wyników dla wybranego parametru.
- **📈 Rozkłady i Benchmarki**: Wykresy pudełkowe (Box Plot) i skrzypcowe (Violin Plot) z podziałem na grupy i płeć.
- **📉 Zależności Bivariate**: Wykresy rozrzutu z linią trendu OLS (np. masa/wzrost vs moc wyskoku).
- **🔥 Macierz Korelacji**: Interaktywna mapa ciepła (heatmap) korelacji między wszystkimi parametrami testu.
- **🛠️ Studio Wykresów (Custom Chart Studio)**: Pełna swoboda w tworzeniu własnych wykresów z dowolnymi osiami i agregacjami.

### 3. 🤖 Lokalna Inteligencja AI (Local Ollama Intelligence)
- **✨ Tailor with AI**: Błyskawiczny audyt semantyczny struktury danych przez model językowy.
- **Adaptacyjny Raport Kliniczno-Sportowy**: Model automatycznie przyjmuje odpowiednią rolę ekspercką (fizjoterapeuta sportowy, biomechanik, fizjolog) i generuje uporządkowany raport diagnostyczny z rekomendacjami treningowo-rehabilitacyjnymi.
- **Prywatność i bezpieczeństwo**: Dane nie opuszczają Twojego komputera — analiza odbywa się w 100% lokalnie.

### 4. 🚀 Zero-Terminal Launch (Windows 1-Click)
- Uruchamianie jednym dwuklikiem za pomocą pliku `run.bat` lub skrótu na pulpicie.
- Skrypt sam sprawdza i w razie potrzeby uruchamia usługę Ollama w tle, po czym otwiera przeglądarkę pod adresem `http://localhost:8501`.

---

## 📁 Struktura Projektu / Project Structure

```
├── inbox/                  # Tutaj wrzucasz nowe pliki (.xlsx, .csv)
│   ├── data_volleyball.xlsx          # Przykładowy zbiór Biodex (izokinetyka)
│   └── eurofit_sportowcy_120.xlsx    # Przykładowy zbiór Eurofit (120 sportowców)
├── processed/              # Zarchiwizowane przetworzone pliki
├── app.py                  # Główna aplikacja Streamlit
├── run.bat                 # Launcher 1-klik dla Windows (cmd)
├── run_silent.vbs          # Opcjonalny cichy launcher bez okna terminala
├── requirements.txt        # Zależności Python
├── .gitignore              # Ignorowane pliki tymczasowe
└── README.md               # Dokumentacja projektu
```

---

## 🛠️ Wymagania i Instalacja / Installation

### 1. Klonowanie repozytorium
```bash
git clone https://github.com/biokineticum/physio-command-center.git
cd physio-command-center
```

### 2. Instalacja zależności Python
Upewnij się, że masz zainstalowanego Pythona (rekomendowany 3.10+):
```bash
pip install -r requirements.txt
```

### 3. Pobranie modelu AI w Ollama
Zainstaluj [Ollama](https://ollama.com/), a następnie pobierz lekki, rekomendowany model:
```bash
ollama pull nemotron-3-nano:4b
```
*(Opcjonalnie możesz użyć dowolnego innego lokalnego modelu, np. `llama3.2:3b`, `qwen2.5:3b`)*.

---

## 🚀 Uruchomienie / Running

### Sposób 1: Przez skrót Windows (bez terminala)
Po prostu kliknij dwukrotnie plik **`run.bat`** w folderze projektu lub skrót na pulpicie.

### Sposób 2: Przez terminal
```bash
streamlit run app.py
```

Aplikacja otworzy się automatycznie w Twojej domyślnej przeglądarce pod adresem:
`http://localhost:8501`

---

## 📄 Licencja / License
MIT License. Created by [biokineticum](https://github.com/biokineticum).
