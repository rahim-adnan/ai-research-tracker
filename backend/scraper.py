# scraper.py — Arxiv Paper Fetcher
#
# Uses requests + BeautifulSoup to parse arxiv RSS directly.
# More reliable than feedparser on Windows.

import requests
from bs4 import BeautifulSoup
import logging
import re
from typing import List
from models import Paper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ARXIV_FEEDS = {
    "cs.AI": "https://rss.arxiv.org/rss/cs.AI",
    "cs.LG": "https://rss.arxiv.org/rss/cs.LG",
    "cs.CL": "https://rss.arxiv.org/rss/cs.CL",
    "cs.CV": "https://rss.arxiv.org/rss/cs.CV",
}

PAPERS_PER_CATEGORY = 10

HEADERS = {
    "User-Agent": "Mozilla/5.0 (research tracker bot)"
}


def fetch_all_papers() -> List[Paper]:
    """Fetches latest papers from all arxiv categories."""
    all_papers = []
    seen_ids = set()

    for category, url in ARXIV_FEEDS.items():
        logger.info(f"Fetching: {category}")
        try:
            papers = fetch_category(category, url)
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


def fetch_category(category: str, url: str) -> List[Paper]:
    """Fetches and parses one arxiv RSS feed."""
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()

    # Parse XML with BeautifulSoup
    soup = BeautifulSoup(response.content, "xml")
    items = soup.find_all("item")[:PAPERS_PER_CATEGORY]

    logger.info(f"Found {len(items)} items in {category} feed")

    papers = []
    for item in items:
        try:
            paper = parse_item(item, category)
            if paper:
                papers.append(paper)
        except Exception as e:
            logger.warning(f"Failed to parse item: {e}")
            continue

    return papers


def parse_item(item, category: str) -> Paper:
    """Converts one RSS <item> into a Paper object."""

    # Title
    title = item.find("title")
    title = title.text.strip() if title else ""
    if not title:
        return None

    # Abstract — in arxiv RSS it's in <description>
    description = item.find("description")
    abstract = description.text.strip() if description else ""
    abstract = clean_text(abstract)

    if len(abstract) < 30:
        return None

    # URL / link
    link = item.find("link")
    if link:
        url = link.text.strip() if link.text else link.get("href", "")
    else:
        url = ""

    # Arxiv ID from URL
    arxiv_id = ""
    if url:
        match = re.search(r'abs/([0-9.]+)', url)
        if match:
            arxiv_id = match.group(1)

    if not arxiv_id:
        # Try guid
        guid = item.find("guid")
        if guid:
            match = re.search(r'abs/([0-9.]+)', guid.text)
            if match:
                arxiv_id = match.group(1)

    # Authors — arxiv uses <dc:creator>
    authors = []
    creator = item.find("creator")
    if creator:
        authors = [a.strip() for a in creator.text.split(",")][:5]

    # Date
    pub_date = item.find("pubDate")
    published = ""
    if pub_date:
        raw = pub_date.text.strip()
        # Format: "Mon, 07 Apr 2025 00:00:00 -0400"
        try:
            from email.utils import parsedate
            from datetime import datetime
            parsed = parsedate(raw)
            if parsed:
                published = f"{parsed[0]}-{parsed[1]:02d}-{parsed[2]:02d}"
        except:
            published = raw[:10]

    return Paper(
        arxiv_id=arxiv_id or title[:20],
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
