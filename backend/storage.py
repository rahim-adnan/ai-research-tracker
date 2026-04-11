# storage.py — Simple JSON Storage
#
# WHAT THIS FILE DOES:
# Saves and loads papers to a local JSON file.
# This means papers persist between server restarts —
# you don't have to re-fetch and re-analyze every time.
#
# WHY JSON AND NOT A DATABASE?
# For this project, a JSON file is perfect:
# - Zero setup (no PostgreSQL, no MongoDB to install)
# - Human readable (you can open it in any text editor)
# - Fast enough for hundreds of papers
# A real production app would use a database, but for learning this is ideal.

import json
import os
import logging
from typing import List, Optional
from datetime import datetime
from models import Paper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to our JSON "database" file
STORAGE_FILE = "papers_db.json"
METADATA_FILE = "metadata.json"


def save_papers(papers: List[Paper]) -> None:
    """
    Saves all papers to the JSON file.
    Overwrites the entire file each time (simple but effective).
    """
    data = [paper.model_dump() for paper in papers]
    with open(STORAGE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(papers)} papers to {STORAGE_FILE}")

    # Update metadata
    save_metadata({"last_updated": datetime.now().isoformat(), "total_papers": len(papers)})


def load_papers() -> List[Paper]:
    """
    Loads all papers from the JSON file.
    Returns empty list if file doesn't exist yet.
    """
    if not os.path.exists(STORAGE_FILE):
        logger.info("No papers file found — starting fresh")
        return []

    try:
        with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        papers = [Paper(**item) for item in data]
        logger.info(f"Loaded {len(papers)} papers from storage")
        return papers
    except Exception as e:
        logger.error(f"Failed to load papers: {e}")
        return []


def save_metadata(meta: dict) -> None:
    """Saves metadata like last update time."""
    with open(METADATA_FILE, 'w') as f:
        json.dump(meta, f, indent=2)


def load_metadata() -> dict:
    """Loads metadata."""
    if not os.path.exists(METADATA_FILE):
        return {"last_updated": "Never", "total_papers": 0}
    try:
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"last_updated": "Never", "total_papers": 0}


def merge_papers(existing: List[Paper], new_papers: List[Paper]) -> List[Paper]:
    """
    Merges new papers into existing list without duplicates.
    Uses arxiv_id as the unique key.

    This way, if you fetch papers daily, you accumulate a growing
    database without re-analyzing papers you've already seen.
    """
    existing_ids = {p.arxiv_id for p in existing}
    added = 0

    for paper in new_papers:
        if paper.arxiv_id not in existing_ids:
            existing.append(paper)
            existing_ids.add(paper.arxiv_id)
            added += 1

    logger.info(f"Added {added} new papers. Total: {len(existing)}")
    return existing


def get_trends(papers: List[Paper]) -> dict:
    """
    Calculates skill and job trends from all processed papers.

    HOW IT WORKS:
    Goes through every paper, collects all skills and jobs mentioned,
    counts how many times each appears, and sorts by frequency.
    This tells us what's trending in AI research right now.
    """
    skill_counts = {}
    rising_counts = {}
    declining_counts = {}

    for paper in papers:
        if not paper.processed:
            continue

        # Count skills
        for skill in (paper.skills or []):
            skill = skill.strip()
            if skill:
                skill_counts[skill] = skill_counts.get(skill, 0) + 1

        # Count rising jobs
        for job in (paper.rising_jobs or []):
            job = job.strip()
            if job:
                rising_counts[job] = rising_counts.get(job, 0) + 1

        # Count declining jobs
        for job in (paper.declining_jobs or []):
            job = job.strip()
            if job:
                declining_counts[job] = declining_counts.get(job, 0) + 1

    # Sort by count, take top results
    top_skills   = sorted([{"skill": k, "count": v} for k, v in skill_counts.items()],
                          key=lambda x: x["count"], reverse=True)[:15]
    top_rising   = sorted([{"job": k, "count": v} for k, v in rising_counts.items()],
                          key=lambda x: x["count"], reverse=True)[:10]
    top_declining = sorted([{"job": k, "count": v} for k, v in declining_counts.items()],
                           key=lambda x: x["count"], reverse=True)[:10]

    meta = load_metadata()

    return {
        "top_skills":    top_skills,
        "rising_jobs":   top_rising,
        "declining_jobs": top_declining,
        "total_papers":  len([p for p in papers if p.processed]),
        "last_updated":  meta.get("last_updated", "Never"),
    }
