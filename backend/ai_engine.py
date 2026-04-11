# ai_engine.py — AI Paper Analyzer
#
# WHAT THIS FILE DOES:
# Takes each paper's abstract and sends it to Ollama (Llama3).
# Extracts exactly 3 things:
#   1. Plain English summary (2-3 sentences)
#   2. Skills this paper is about / requires
#   3. Jobs rising or declining because of this research
#
# WHY ABSTRACTS ONLY?
# Full papers are 10-20 pages — too slow on CPU.
# Abstracts are 150-300 words — fast and contain ALL the key info.
# Researchers write abstracts to summarize everything important.

import requests
import re
import logging
from typing import List
from models import Paper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OLLAMA_URL  = "http://localhost:11434/api/generate"
MODEL_NAME  = "llama3"


def check_ollama() -> bool:
    """Check if Ollama is running."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = [m["name"] for m in response.json().get("models", [])]
            logger.info(f"Ollama running. Models: {models}")
            if not any(MODEL_NAME in m for m in models):
                logger.warning(f"'{MODEL_NAME}' not found! Run: ollama pull {MODEL_NAME}")
                return False
            return True
    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to Ollama. Is it running?")
        return False
    return False


def call_ollama(prompt: str, max_tokens: int = 300) -> str:
    """Sends a prompt to local Ollama and returns response."""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": 0.3,   # low temperature = more consistent, structured output
            "top_p": 0.9,
        }
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()["response"].strip()
    except requests.exceptions.Timeout:
        raise RuntimeError("Ollama timed out")
    except Exception as e:
        raise RuntimeError(f"Ollama error: {str(e)}")


def analyze_paper(paper: Paper) -> Paper:
    """
    Analyzes one paper and fills in the AI-generated fields.
    Uses a single focused prompt to extract all 3 things at once.
    Returns the same paper object with fields filled in.
    """
    logger.info(f"Analyzing: {paper.title[:60]}...")

    prompt = f"""You are an AI research analyst. Read this research paper abstract and extract key information.

Paper Title: {paper.title}

Abstract: {paper.abstract}

Respond in EXACTLY this format, nothing else:

SUMMARY: Write 2 sentences explaining what this paper does in plain English that anyone can understand.

SKILLS: List 4-6 specific technical skills this research involves or that professionals need to work with it. Separate with commas.

RISING_JOBS: List 2-3 job roles that will GROW because of research like this. Separate with commas.

DECLINING_JOBS: List 1-2 job roles that AI/automation from research like this might REPLACE or REDUCE. Separate with commas. Write "None" if not applicable.

IMPACT: Write exactly one word — High, Medium, or Low — based on how much this could change the industry."""

    try:
        raw = call_ollama(prompt, max_tokens=300)
        result = parse_analysis(raw)

        paper.summary        = result["summary"]
        paper.skills         = result["skills"]
        paper.rising_jobs    = result["rising_jobs"]
        paper.declining_jobs = result["declining_jobs"]
        paper.impact_level   = result["impact_level"]
        paper.processed      = True

    except Exception as e:
        logger.error(f"Failed to analyze paper '{paper.title[:40]}': {e}")
        # Fill with fallback values so the paper still shows up
        paper.summary        = paper.abstract[:200] + "..."
        paper.skills         = extract_skills_simple(paper.abstract)
        paper.rising_jobs    = ["AI/ML Engineer"]
        paper.declining_jobs = []
        paper.impact_level   = "Medium"
        paper.processed      = True

    return paper


def parse_analysis(raw: str) -> dict:
    """Parses Ollama's structured output into a clean dictionary."""

    def extract(label: str) -> str:
        pattern = rf"{label}:\s*(.+?)(?=\n[A-Z_]{{3,}}:|$)"
        match = re.search(pattern, raw, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""

    def to_list(text: str) -> List[str]:
        """Converts comma-separated string to cleaned list."""
        if not text or text.lower() == "none":
            return []
        items = [item.strip() for item in re.split(r'[,\n]', text)]
        return [i for i in items if i and len(i) > 2][:6]

    summary        = extract("SUMMARY")       or "This paper presents advances in AI research."
    skills_raw     = extract("SKILLS")        or "Python, Machine Learning"
    rising_raw     = extract("RISING_JOBS")   or "AI Engineer"
    declining_raw  = extract("DECLINING_JOBS") or ""
    impact_raw     = extract("IMPACT")        or "Medium"

    # Clean up impact level
    impact = "Medium"
    for level in ["High", "Medium", "Low"]:
        if level.lower() in impact_raw.lower():
            impact = level
            break

    return {
        "summary":       summary,
        "skills":        to_list(skills_raw),
        "rising_jobs":   to_list(rising_raw),
        "declining_jobs": to_list(declining_raw),
        "impact_level":  impact,
    }


def extract_skills_simple(text: str) -> List[str]:
    """
    Simple keyword-based skill extractor used as fallback.
    Looks for known AI/ML skill keywords in the abstract.
    """
    known_skills = [
        "Python", "PyTorch", "TensorFlow", "JAX",
        "transformer", "fine-tuning", "RAG", "RLHF",
        "LLM", "diffusion", "embeddings", "vector database",
        "reinforcement learning", "computer vision", "NLP",
        "multimodal", "agent", "prompt engineering",
        "knowledge graph", "neural network", "deep learning",
    ]
    found = []
    text_lower = text.lower()
    for skill in known_skills:
        if skill.lower() in text_lower:
            found.append(skill)
    return found[:6] if found else ["Machine Learning", "Python"]


def analyze_all_papers(papers: List[Paper]) -> List[Paper]:
    """
    Analyzes a list of papers one by one.
    Skips papers that are already processed.
    """
    to_process = [p for p in papers if not p.processed]
    logger.info(f"Analyzing {len(to_process)} new papers...")

    for i, paper in enumerate(to_process):
        logger.info(f"Processing {i+1}/{len(to_process)}: {paper.title[:50]}...")
        paper = analyze_paper(paper)

    logger.info("All papers analyzed!")
    return papers
