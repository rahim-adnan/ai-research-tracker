# ai_engine.py — AI Paper Analyzer (Groq version)
#
# Same as before but uses Groq's free API instead of local Ollama.
# Model: llama3-8b-8192 — same Llama3, runs in the cloud for free.

import requests
import re
import logging
import os
from typing import List
from models import Paper
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"
MODEL_NAME   = "llama3-8b-8192"


def check_ollama() -> bool:
    """Check if Groq API key is available."""
    if not GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not found in environment!")
        return False
    logger.info("Groq API key found — ready to analyze.")
    return True


def call_ollama(prompt: str, max_tokens: int = 300) -> str:
    """Sends prompt to Groq and returns response. Same interface as before."""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.3,
    }
    try:
        response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.Timeout:
        raise RuntimeError("Groq timed out")
    except Exception as e:
        raise RuntimeError(f"Groq error: {str(e)}")


def analyze_paper(paper: Paper) -> Paper:
    """
    Analyzes one paper and fills in the AI-generated fields.
    Uses a single focused prompt to extract all 3 things at once.
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
        logger.error(f"Failed to analyze '{paper.title[:40]}': {e}")
        paper.summary        = paper.abstract[:200] + "..."
        paper.skills         = extract_skills_simple(paper.abstract)
        paper.rising_jobs    = ["AI/ML Engineer"]
        paper.declining_jobs = []
        paper.impact_level   = "Medium"
        paper.processed      = True

    return paper


def parse_analysis(raw: str) -> dict:
    """Parses Groq's structured output into a clean dictionary."""

    def extract(label: str) -> str:
        pattern = rf"{label}:\s*(.+?)(?=\n[A-Z_]{{3,}}:|$)"
        match = re.search(pattern, raw, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""

    def to_list(text: str) -> List[str]:
        if not text or text.lower() == "none":
            return []
        items = [item.strip() for item in re.split(r'[,\n]', text)]
        return [i for i in items if i and len(i) > 2][:6]

    summary       = extract("SUMMARY")        or "This paper presents advances in AI research."
    skills_raw    = extract("SKILLS")         or "Python, Machine Learning"
    rising_raw    = extract("RISING_JOBS")    or "AI Engineer"
    declining_raw = extract("DECLINING_JOBS") or ""
    impact_raw    = extract("IMPACT")         or "Medium"

    impact = "Medium"
    for level in ["High", "Medium", "Low"]:
        if level.lower() in impact_raw.lower():
            impact = level
            break

    return {
        "summary":        summary,
        "skills":         to_list(skills_raw),
        "rising_jobs":    to_list(rising_raw),
        "declining_jobs": to_list(declining_raw),
        "impact_level":   impact,
    }


def extract_skills_simple(text: str) -> List[str]:
    """Fallback keyword-based skill extractor."""
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
    """Analyzes all unprocessed papers one by one."""
    to_process = [p for p in papers if not p.processed]
    logger.info(f"Analyzing {len(to_process)} new papers...")

    for i, paper in enumerate(to_process):
        logger.info(f"Processing {i+1}/{len(to_process)}: {paper.title[:50]}...")
        paper = analyze_paper(paper)

    logger.info("All papers analyzed!")
    return papers