# models.py — Data Shapes
#
# Defines what a "paper" looks like in our system.
# Every paper goes through these shapes as it moves
# from arxiv → scraper → AI → frontend.

from pydantic import BaseModel
from typing import List, Optional


class Paper(BaseModel):
    """
    Represents one AI research paper.
    This is the core data shape of the entire app.
    """
    arxiv_id: str                        # e.g. "2401.12345"
    title: str                           # full paper title
    abstract: str                        # original abstract text
    authors: List[str]                   # list of author names
    published: str                       # date string e.g. "2024-01-15"
    url: str                             # link to arxiv page
    category: str                        # e.g. "cs.AI", "cs.LG"

    # AI-generated fields (filled after Ollama processes the paper)
    summary: Optional[str] = None        # 2-3 sentence plain English summary
    skills: Optional[List[str]] = None   # e.g. ["Python", "RAG", "fine-tuning"]
    rising_jobs: Optional[List[str]] = None   # jobs this paper suggests are growing
    declining_jobs: Optional[List[str]] = None  # jobs AI might replace
    impact_level: Optional[str] = None  # "High" / "Medium" / "Low"
    processed: bool = False              # has Ollama analyzed this yet?


class FetchResponse(BaseModel):
    """Returned by /fetch-papers"""
    success: bool
    papers_found: int
    message: str


class AnalyzeResponse(BaseModel):
    """Returned by /analyze-papers"""
    success: bool
    papers_analyzed: int
    message: str


class TrendsResponse(BaseModel):
    """Returned by /get-trends"""
    top_skills: List[dict]        # [{"skill": "RAG", "count": 12}, ...]
    rising_jobs: List[dict]       # [{"job": "LLM Engineer", "count": 8}, ...]
    declining_jobs: List[dict]
    total_papers: int
    last_updated: str
