# 🔬 AI Research Tracker

Stay up to date with the latest AI research — without reading every paper.
Automatically fetches papers from arxiv, summarizes them with Llama3,
and shows you exactly which skills are rising and which jobs are at risk.

**100% free. Runs locally. No API key needed.**

---

## ✨ Features

- **Auto-fetch** — grabs today's papers from arxiv cs.AI, cs.LG, cs.CL, cs.CV
- **Plain English summaries** — no PhD required to understand
- **Skill extraction** — which technologies appear most in research
- **Job impact** — which roles are rising or declining
- **Impact rating** — High / Medium / Low per paper
- **Persistent storage** — papers saved locally, never re-analyzed twice
- **Filter by category** — view only AI, ML, NLP, or CV papers
- **Clickable links** — go straight to the full paper on arxiv

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | Streamlit | Dashboard UI |
| Backend | FastAPI | REST API server |
| AI Model | Llama3 via Ollama | Local summarization + skill extraction |
| Scraping | requests + BeautifulSoup | Arxiv RSS feed parsing |
| Storage | JSON file | Local paper database |
| Validation | Pydantic | Data schemas |

---

## 📁 Project Structure

```
ai-research-tracker/
├── backend/
│   ├── main.py          # FastAPI server — 5 endpoints
│   ├── scraper.py       # Arxiv RSS fetcher
│   ├── ai_engine.py     # Ollama analysis + prompt engineering
│   ├── storage.py       # JSON read/write + trend calculation
│   └── models.py        # Pydantic data schemas
├── frontend/
│   ├── app.py           # Streamlit UI — 3 tabs
│   └── config.py        # API URLs and settings
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🚀 Setup & Run

### Prerequisites
- Python 3.9+
- Ollama installed with Llama3
- ~500MB free space

### Step 1 — Clone the repo
```bash
git clone https://github.com/rahim-adnan/ai-research-tracker.git
cd ai-research-tracker
```

### Step 2 — Create virtual environment
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
pip install lxml
```

### Step 4 — Make sure Ollama + Llama3 is ready
```bash
# Download from https://ollama.com then:
ollama pull llama3
```

### Step 5 — Start backend (Terminal 1)
```bash
cd backend
python main.py
```
Wait for: `Server ready!`

### Step 6 — Start frontend (Terminal 2)
```bash
cd frontend
streamlit run app.py
```
Opens at: `http://localhost:8501`

### Step 7 — Use it
1. Go to **⚙️ Control** tab
2. Click **Fetch Papers** — gets today's papers (~10 sec)
3. Click **Analyze Papers** — Llama3 reads each paper (~1-2 min per paper)
4. Go to **📊 Dashboard** — see skill and job trends
5. Go to **📄 Papers** — read plain English summaries

---

## ⚡ Performance

| Step | Time |
|---|---|
| Fetch papers | ~10 seconds |
| Analyze 1 paper | 60–120 seconds on CPU |
| Analyze 40 papers | ~60–80 minutes |
| Loading dashboard | Instant |

Run fetch + analyze once, then just re-fetch weekly.
Already-analyzed papers are never re-processed.

---

## ⚠️ Troubleshooting

| Problem | Solution |
|---|---|
| Backend offline | Run `python main.py` in backend folder |
| Ollama not connected | Start Ollama or run `ollama serve` |
| Only 1 paper fetched | Make sure `lxml` is installed: `pip install lxml` |
| No papers showing | Go to Control tab → Fetch Papers first |
| Analysis timed out | Still running in background — wait and refresh |
| `ModuleNotFoundError` | Activate venv + `pip install -r requirements.txt` |

---

## 🔮 Future Improvements

- [ ] Daily auto-fetch (no manual button)
- [ ] Email digest — weekly summary in your inbox
- [ ] Search papers by keyword
- [ ] Save favourite papers
- [ ] Export trends as PDF
- [ ] Add Papers With Code as extra source

---

## 👤 Author

Built by [rahim-adnan](https://github.com/rahim-adnan).
Powered by Arxiv + Ollama Llama3. 100% free and open source.

---

## 📄 License

MIT License — free to use, modify, and distribute.
