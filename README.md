# Physio & Sports Command Center

**Universal adaptive biomechanical and fitness analytics** — drop Excel/CSV into `inbox/`, get dynamic charts and a local AI report.

For physiotherapists, coaches, sports scientists and researchers who need quick group/individual profiles from Eurofit, isokinetics, force plates, GPS or similar test batteries — without forcing a fixed column schema.

## Features

- **Schema profiling** — auto-detects IDs, categories and numeric metrics from `.xlsx` / `.csv` in `inbox/`
- **Visual suite** — percentile radar, rankings, box/violin plots, OLS scatter, correlation heatmap, custom chart studio (Plotly)
- **Local AI (Ollama)** — semantic data audit and clinical/sports-style reports; data stays on your machine
- **One-click Windows launch** — `run.bat` / `run_silent.vbs` start Streamlit at `http://localhost:8501`

## Requirements

- Python 3.10+ (3.11+ recommended)
- [Ollama](https://ollama.com/) for AI features (optional but recommended)

## Install & quick start

```bash
git clone https://github.com/biokineticum/physio-command-center.git
cd physio-command-center
pip install -r requirements.txt
```

Pull a local model (example used in docs):

```bash
ollama pull nemotron-3-nano:4b
```

Run:

```bash
streamlit run app.py
```

On Windows you can also double-click `run.bat`. Put sample or your own files in `inbox/` (repo includes `data_volleyball.xlsx` and `eurofit_sportowcy_120.xlsx`).

## Project layout

```
inbox/           # drop .xlsx / .csv here
app.py           # Streamlit app
run.bat          # Windows launcher
requirements.txt
```

---

## Author

**Dariusz Mosler** (Biokineticum) — physiotherapy, biomechanics, sports science  
🌐 [biokineticum.com](https://biokineticum.com) · 📰 [Substack](https://biokineticum.substack.com) · 𝕏 [@Biokineticum](https://x.com/Biokineticum)

