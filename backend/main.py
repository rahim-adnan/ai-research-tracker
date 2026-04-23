# main.py — FastAPI Server
#
# ENDPOINTS:
#   GET  /health            → is server alive?
#   POST /fetch-papers      → scrape latest papers from arxiv
#   POST /analyze-papers    → run AI on unprocessed papers
#   POST /analyze-one       → analyze just ONE paper (avoids timeout)
#   GET  /get-papers        → return all stored papers
#   GET  /get-trends        → return skill + job trends
#   POST /full-refresh      → fetch + analyze in one call

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from models import FetchResponse, AnalyzeResponse, TrendsResponse
from scraper import fetch_all_papers
from ai_engine import check_ollama, analyze_all_papers, analyze_paper
from storage import load_papers, save_papers, merge_papers, get_trends

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory paper store — loaded from file on startup
papers_store = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    global papers_store
    logger.info("Server starting...")
    logger.info("Loading saved papers from storage...")
    papers_store = load_papers()
    logger.info(f"Loaded {len(papers_store)} papers")

    groq_ok = check_ollama()
    if not groq_ok:
        logger.warning("Groq API key not found — analysis features will fail.")

    logger.info("Server ready!")
    yield
    # SHUTDOWN
    logger.info("Saving papers before shutdown...")
    save_papers(papers_store)


app = FastAPI(
    title="AI Research Tracker API",
    description="Track latest AI research papers and extract skill trends",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── HEALTH ────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    groq_ok = check_ollama()
    return {
        "status": "healthy",
        "papers_in_store": len(papers_store),
        "groq_connected": groq_ok,
    }


# ── FETCH PAPERS ──────────────────────────────────────────────────────

@app.post("/fetch-papers", response_model=FetchResponse)
async def fetch_papers():
    """
    Scrapes latest papers from arxiv RSS feeds.
    Merges them into the existing store (no duplicates).
    Does NOT analyze them yet — call /analyze-one for that.
    """
    global papers_store
    try:
        logger.info("Fetching papers from arxiv...")
        new_papers = fetch_all_papers()
        before = len(papers_store)
        papers_store = merge_papers(papers_store, new_papers)
        added = len(papers_store) - before
        save_papers(papers_store)

        return FetchResponse(
            success=True,
            papers_found=added,
            message=f"Fetched {len(new_papers)} papers, {added} were new."
        )
    except Exception as e:
        logger.error(f"Fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── ANALYZE ONE PAPER ─────────────────────────────────────────────────

@app.post("/analyze-one")
async def analyze_one():
    """
    Analyzes just ONE unprocessed paper per call.
    Call this repeatedly from the frontend to avoid timeouts.
    Much more reliable than analyzing all papers at once.
    """
    global papers_store
    unprocessed = [p for p in papers_store if not p.processed]

    if not unprocessed:
        return {
            "success": True,
            "done": True,
            "remaining": 0,
            "message": "All papers are already analyzed!"
        }

    # Analyze just the first unprocessed paper
    paper = unprocessed[0]
    logger.info(f"Analyzing one paper: {paper.title[:60]}...")
    paper = analyze_paper(paper)
    save_papers(papers_store)

    remaining = len([p for p in papers_store if not p.processed])
    return {
        "success": True,
        "done": remaining == 0,
        "remaining": remaining,
        "analyzed_title": paper.title[:60],
        "message": f"Analyzed 1 paper. {remaining} remaining."
    }


# ── ANALYZE ALL PAPERS (kept for reference) ───────────────────────────

@app.post("/analyze-papers", response_model=AnalyzeResponse)
async def analyze_papers():
    """
    Runs Groq AI on all unprocessed papers at once.
    May timeout on Render free tier if there are many papers.
    Use /analyze-one instead for reliability.
    """
    global papers_store
    unprocessed = [p for p in papers_store if not p.processed]

    if not unprocessed:
        return AnalyzeResponse(
            success=True,
            papers_analyzed=0,
            message="All papers are already analyzed!"
        )

    try:
        logger.info(f"Analyzing {len(unprocessed)} papers...")
        papers_store = analyze_all_papers(papers_store)
        save_papers(papers_store)

        analyzed = len([p for p in papers_store if p.processed])
        return AnalyzeResponse(
            success=True,
            papers_analyzed=len(unprocessed),
            message=f"Successfully analyzed {len(unprocessed)} papers. Total analyzed: {analyzed}"
        )
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── GET PAPERS ────────────────────────────────────────────────────────

@app.get("/get-papers")
async def get_papers(limit: int = 50, category: str = None, processed_only: bool = False):
    """
    Returns stored papers with optional filtering.
    - limit: max number of papers to return
    - category: filter by arxiv category (cs.AI, cs.LG, etc.)
    - processed_only: only return papers that have been analyzed
    """
    filtered = papers_store

    if category:
        filtered = [p for p in filtered if p.category == category]

    if processed_only:
        filtered = [p for p in filtered if p.processed]

    # Sort by date — newest first
    filtered = sorted(filtered, key=lambda p: p.published, reverse=True)

    return {
        "papers": [p.model_dump() for p in filtered[:limit]],
        "total": len(filtered)
    }


# ── GET TRENDS ────────────────────────────────────────────────────────

@app.get("/get-trends")
async def get_trends_endpoint():
    """
    Returns aggregated skill and job trends across all analyzed papers.
    This is the key insight endpoint — what skills are rising/falling?
    """
    if not papers_store:
        raise HTTPException(status_code=404, detail="No papers found. Run /fetch-papers first.")

    trends = get_trends(papers_store)
    return trends


# ── FULL REFRESH ──────────────────────────────────────────────────────

@app.post("/full-refresh")
async def full_refresh():
    """
    Convenience endpoint: fetch new papers AND analyze them in one call.
    Warning: May timeout on free tier. Use fetch + analyze-one instead.
    """
    global papers_store

    # Step 1: Fetch
    new_papers = fetch_all_papers()
    before = len(papers_store)
    papers_store = merge_papers(papers_store, new_papers)
    added = len(papers_store) - before

    # Step 2: Analyze
    papers_store = analyze_all_papers(papers_store)
    save_papers(papers_store)

    return {
        "success": True,
        "new_papers_added": added,
        "total_papers": len(papers_store),
        "analyzed": len([p for p in papers_store if p.processed])
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)