# config.py — Frontend Settings

API_BASE_URL      = "http://localhost:8000"
FETCH_ENDPOINT    = f"{API_BASE_URL}/fetch-papers"
ANALYZE_ENDPOINT  = f"{API_BASE_URL}/analyze-papers"
PAPERS_ENDPOINT   = f"{API_BASE_URL}/get-papers"
TRENDS_ENDPOINT   = f"{API_BASE_URL}/get-trends"
REFRESH_ENDPOINT  = f"{API_BASE_URL}/full-refresh"
HEALTH_ENDPOINT   = f"{API_BASE_URL}/health"

REQUEST_TIMEOUT   = 300   # 5 minutes — analysis is slow on CPU

CATEGORIES = {
    "All":    None,
    "cs.AI":  "Artificial Intelligence",
    "cs.LG":  "Machine Learning",
    "cs.CL":  "NLP / Language",
    "cs.CV":  "Computer Vision",
}

IMPACT_COLORS = {
    "High":   "#dc3545",   # red
    "Medium": "#fd7e14",   # orange
    "Low":    "#28a745",   # green
}
