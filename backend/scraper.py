# scraper.py — Arxiv Paper Fetcher
# Uses arxiv API to fetch papers from the last 7 days.

import requests
from bs4 import BeautifulSoup
import logging
import re
from typing import List
from models import Paper
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CATEGORIES = ["cs.AI", "cs.LG", "cs.CL", "cs.CV"]
PAPERS_PER_CATEGORY = 10

HEADERS = {
    "User-Agent": "Mozilla/5.0 (research tracker bot)"
}


def fetch_all_papers() -> List[Paper]:
    """Fetches papers from the last 7 days across all categories."""
    all_papers = []
    seen_ids = set()

    for category in CATEGORIES:
        logger.info(f"Fetching: {category}")
        try:
            papers = fetch_category(category)
            for paper in papers:
                if paper.arxiv_id not in seen_ids:
                    all_papers.append(paper)
                    seen_ids.add(paper.arxiv_id)
            logger.info(f"Got {len(papers)} papers from {category}")
        except Exception as e:
            logger.error(f"Failed {category}: {e}")
            continue

    logger.info(f"Total papers fetched: {len(all_papers)}")
    return all_papers


def fetch_category(category: str) -> List[Paper]:
    """Fetches papers using arxiv API with a 7-day window."""
    url = "https://export.arxiv.org/api/query"
    params = {
        "search_query": f"cat:{category}",
        "start": 0,
        "max_results": PAPERS_PER_CATEGORY,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }

    response = requests.get(url, params=params, headers=HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "xml")
    entries = soup.find_all("entry")
    logger.info(f"Found {len(entries)} items in {category} feed")

    papers = []
    cutoff = datetime.now() - timedelta(days=7)

    for entry in entries:
        try:
            paper = parse_entry(entry, category, cutoff)
            if paper:
                papers.append(paper)
        except Exception as e:
            logger.warning(f"Failed to parse entry: {e}")
            continue

    return papers


def parse_entry(entry, category: str, cutoff: datetime) -> Paper:
    """Converts one API entry into a Paper object."""

    title = entry.find("title")
    title = title.text.strip().replace("\n", " ") if title else ""
    if not title:
        return None

    abstract = entry.find("summary")
    abstract = abstract.text.strip() if abstract else ""
    abstract = clean_text(abstract)
    if len(abstract) < 30:
        return None

    # URL and arxiv ID
    id_tag = entry.find("id")
    url = id_tag.text.strip() if id_tag else ""
    arxiv_id = ""
    if url:
        match = re.search(r'abs/([0-9.]+)', url)
        if match:
            arxiv_id = match.group(1)

    if not arxiv_id:
        return None

    # Authors
    authors = []
    for author in entry.find_all("author"):
        name = author.find("name")
        if name:
            authors.append(name.text.strip())
    authors = authors[:5]

    # Published date
    published_tag = entry.find("published")
    published = ""
    if published_tag:
        raw = published_tag.text.strip()
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            published = dt.strftime("%Y-%m-%d")
            if dt.replace(tzinfo=None) < cutoff:
                return None
        except:
            published = raw[:10]

    return Paper(
        arxiv_id=arxiv_id,
        title=title,
        abstract=abstract,
        authors=authors,
        published=published,
        url=url,
        category=category,
        processed=False
    )


def clean_text(text: str) -> str:
    """Removes HTML tags and normalizes whitespace."""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()