# app.py — AI Research Tracker Frontend
#
# THREE TABS:
#   Tab 1 — Dashboard   : skill trends, job trends, key numbers
#   Tab 2 — Papers      : browse all fetched papers with summaries
#   Tab 3 — Control     : fetch new papers, trigger analysis

import streamlit as st
import requests
from config import (
    FETCH_ENDPOINT, ANALYZE_ENDPOINT, PAPERS_ENDPOINT,
    TRENDS_ENDPOINT, HEALTH_ENDPOINT, REQUEST_TIMEOUT,
    CATEGORIES, IMPACT_COLORS
)

# ── PAGE CONFIG ───────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Research Tracker",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── CUSTOM CSS ────────────────────────────────────────────────────────

st.markdown("""
<style>
    .paper-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        margin: 12px 0;
        border-left: 4px solid #4A90D9;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    }
    .paper-title {
        font-size: 16px;
        font-weight: 600;
        color: #1a1a2e;
        margin-bottom: 6px;
    }
    .paper-meta {
        font-size: 12px;
        color: #888;
        margin-bottom: 10px;
    }
    .paper-summary {
        font-size: 14px;
        color: #333;
        line-height: 1.6;
        margin-bottom: 12px;
    }
    .skill-tag {
        display: inline-block;
        background: #e8f0fe;
        color: #1a56db;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 12px;
        margin: 2px;
        font-weight: 500;
    }
    .rising-tag {
        display: inline-block;
        background: #d4edda;
        color: #155724;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 12px;
        margin: 2px;
        font-weight: 500;
    }
    .declining-tag {
        display: inline-block;
        background: #f8d7da;
        color: #721c24;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 12px;
        margin: 2px;
        font-weight: 500;
    }
    .impact-high   { color: #dc3545; font-weight: 700; }
    .impact-medium { color: #fd7e14; font-weight: 700; }
    .impact-low    { color: #28a745; font-weight: 700; }
    .trend-bar-skill {
        background: linear-gradient(90deg, #4A90D9, #7BB3F0);
        height: 28px;
        border-radius: 4px;
        display: flex;
        align-items: center;
        padding: 0 10px;
        color: white;
        font-size: 13px;
        font-weight: 500;
        margin: 3px 0;
    }
    .trend-bar-rising {
        background: linear-gradient(90deg, #28a745, #5cb85c);
        height: 28px;
        border-radius: 4px;
        display: flex;
        align-items: center;
        padding: 0 10px;
        color: white;
        font-size: 13px;
        font-weight: 500;
        margin: 3px 0;
    }
    .trend-bar-declining {
        background: linear-gradient(90deg, #dc3545, #e87070);
        height: 28px;
        border-radius: 4px;
        display: flex;
        align-items: center;
        padding: 0 10px;
        color: white;
        font-size: 13px;
        font-weight: 500;
        margin: 3px 0;
    }
</style>
""", unsafe_allow_html=True)


# ── HELPERS ───────────────────────────────────────────────────────────

def check_health():
    try:
        r = requests.get(HEALTH_ENDPOINT, timeout=5)
        return r.status_code == 200, r.json()
    except:
        return False, {}


def fetch_papers():
    r = requests.post(FETCH_ENDPOINT, timeout=60)
    r.raise_for_status()
    return r.json()


def analyze_papers():
    r = requests.post(ANALYZE_ENDPOINT, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.json()


def get_papers(category=None, processed_only=False):
    params = {"limit": 100, "processed_only": processed_only}
    if category:
        params["category"] = category
    r = requests.get(PAPERS_ENDPOINT, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def get_trends():
    r = requests.get(TRENDS_ENDPOINT, timeout=30)
    r.raise_for_status()
    return r.json()


def render_skill_tags(skills):
    if not skills:
        return ""
    tags = "".join([f'<span class="skill-tag">{s}</span>' for s in skills])
    return tags


def render_job_tags(jobs, tag_class):
    if not jobs:
        return '<span style="color:#aaa; font-size:12px;">None identified</span>'
    tags = "".join([f'<span class="{tag_class}">{j}</span>' for j in jobs])
    return tags


# ── HEADER ────────────────────────────────────────────────────────────

st.markdown("""
<div style="text-align:center; padding: 20px 0 5px;">
    <h1>🔬 AI Research Tracker</h1>
    <p style="color:#666; font-size:16px;">
        Latest AI research papers → plain English summaries → skills & job trends
    </p>
</div>
""", unsafe_allow_html=True)

# Backend status
ok, health_data = check_health()
col_s, _ = st.columns([1, 3])
with col_s:
    if ok:
        papers_count = health_data.get("papers_in_store", 0)
        st.markdown(f'<p style="color:#28a745; font-weight:600;">● Backend connected · {papers_count} papers stored</p>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<p style="color:#dc3545; font-weight:600;">● Backend offline — run: cd backend && python main.py</p>',
                    unsafe_allow_html=True)

st.divider()


# ── TABS ──────────────────────────────────────────────────────────────

tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📄 Papers", "⚙️ Control"])


# ════════════════════════════════════════════════════════════════════
# TAB 1 — DASHBOARD
# ════════════════════════════════════════════════════════════════════

with tab1:
    st.markdown("### 📊 Trends from Latest AI Research")

    if not ok:
        st.warning("Backend is offline. Start the backend first.")
    else:
        try:
            trends = get_trends()

            # ── Key metrics ──
            col1, col2, col3 = st.columns(3)
            col1.metric("📄 Papers Analyzed", trends.get("total_papers", 0))
            col2.metric("🔧 Unique Skills Found", len(trends.get("top_skills", [])))
            col3.metric("📈 Rising Job Roles", len(trends.get("rising_jobs", [])))

            last_updated = trends.get("last_updated", "Never")
            if last_updated != "Never":
                last_updated = last_updated[:19].replace("T", " ")
            st.caption(f"Last updated: {last_updated}")

            st.divider()

            # ── Trends columns ──
            col_a, col_b, col_c = st.columns(3)

            with col_a:
                st.markdown("#### 🔧 Top Skills to Learn")
                st.caption("Skills most mentioned in recent AI papers")
                skills = trends.get("top_skills", [])
                if skills:
                    max_count = skills[0]["count"] if skills else 1
                    for item in skills[:10]:
                        pct = int((item["count"] / max_count) * 100)
                        width = max(pct, 20)
                        st.markdown(f"""
                        <div style="margin:3px 0;">
                            <div class="trend-bar-skill" style="width:{width}%">
                                {item['skill']} ({item['count']})
                            </div>
                        </div>""", unsafe_allow_html=True)
                else:
                    st.info("No skill data yet. Analyze some papers first.")

            with col_b:
                st.markdown("#### 📈 Rising Job Roles")
                st.caption("Jobs growing due to AI research")
                rising = trends.get("rising_jobs", [])
                if rising:
                    max_count = rising[0]["count"] if rising else 1
                    for item in rising[:8]:
                        pct = int((item["count"] / max_count) * 100)
                        width = max(pct, 20)
                        st.markdown(f"""
                        <div style="margin:3px 0;">
                            <div class="trend-bar-rising" style="width:{width}%">
                                {item['job']} ({item['count']})
                            </div>
                        </div>""", unsafe_allow_html=True)
                else:
                    st.info("No job trend data yet.")

            with col_c:
                st.markdown("#### 📉 Declining / At-Risk Roles")
                st.caption("Jobs AI research may replace")
                declining = trends.get("declining_jobs", [])
                if declining:
                    max_count = declining[0]["count"] if declining else 1
                    for item in declining[:8]:
                        pct = int((item["count"] / max_count) * 100)
                        width = max(pct, 20)
                        st.markdown(f"""
                        <div style="margin:3px 0;">
                            <div class="trend-bar-declining" style="width:{width}%">
                                {item['job']} ({item['count']})
                            </div>
                        </div>""", unsafe_allow_html=True)
                else:
                    st.info("No declining job data yet.")

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                st.info("📭 No papers analyzed yet.\n\nGo to the **⚙️ Control** tab → click **Fetch Papers** → then **Analyze Papers**.")
            else:
                st.error(f"Error: {e}")
        except Exception as e:
            st.error(f"Could not load trends: {e}")


# ════════════════════════════════════════════════════════════════════
# TAB 2 — PAPERS
# ════════════════════════════════════════════════════════════════════

with tab2:
    st.markdown("### 📄 Latest AI Research Papers")

    # Filters
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        cat_label = st.selectbox("Filter by category:", list(CATEGORIES.keys()))
        cat_value = CATEGORIES[cat_label]
    with col2:
        show_only_analyzed = st.checkbox("Analyzed only", value=True)
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        refresh_list = st.button("🔄 Refresh list")

    if not ok:
        st.warning("Backend is offline.")
    else:
        try:
            data = get_papers(category=cat_value, processed_only=show_only_analyzed)
            papers = data.get("papers", [])
            total  = data.get("total", 0)

            st.caption(f"Showing {len(papers)} of {total} papers")

            if not papers:
                st.info("No papers found. Go to ⚙️ Control tab to fetch and analyze papers.")
            else:
                for paper in papers:
                    impact = paper.get("impact_level", "Medium")
                    impact_class = f"impact-{impact.lower()}" if impact else "impact-medium"

                    skills_html   = render_skill_tags(paper.get("skills") or [])
                    rising_html   = render_job_tags(paper.get("rising_jobs") or [], "rising-tag")
                    declining_html = render_job_tags(paper.get("declining_jobs") or [], "declining-tag")

                    authors = paper.get("authors", [])
                    authors_str = ", ".join(authors[:3])
                    if len(authors) > 3:
                        authors_str += f" +{len(authors)-3} more"

                    summary = paper.get("summary") or paper.get("abstract", "")[:200] + "..."

                    st.markdown(f"""
                    <div class="paper-card">
                        <div class="paper-title">
                            <a href="{paper.get('url','#')}" target="_blank" style="color:#1a1a2e; text-decoration:none;">
                                {paper.get('title','Untitled')}
                            </a>
                        </div>
                        <div class="paper-meta">
                            📅 {paper.get('published','')} &nbsp;|&nbsp;
                            🏷️ {paper.get('category','')} &nbsp;|&nbsp;
                            👤 {authors_str} &nbsp;|&nbsp;
                            Impact: <span class="{impact_class}">{impact}</span>
                        </div>
                        <div class="paper-summary">{summary}</div>
                        <div style="margin-bottom:6px;">
                            <strong style="font-size:12px; color:#555;">🔧 Skills:</strong><br>
                            {skills_html if skills_html else '<span style="color:#aaa;font-size:12px;">Not yet analyzed</span>'}
                        </div>
                        <div style="margin-bottom:4px;">
                            <strong style="font-size:12px; color:#555;">📈 Rising roles:</strong> {rising_html}
                        </div>
                        <div>
                            <strong style="font-size:12px; color:#555;">📉 At-risk roles:</strong> {declining_html}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Could not load papers: {e}")


# ════════════════════════════════════════════════════════════════════
# TAB 3 — CONTROL
# ════════════════════════════════════════════════════════════════════

with tab3:
    st.markdown("### ⚙️ Control Panel")

    st.markdown("""
    **How it works — run in this order:**
    1. **Fetch Papers** — downloads latest papers from arxiv (fast, ~10 seconds)
    2. **Analyze Papers** — runs Llama3 on each paper (slow, ~1-2 min per paper)
    """)

    st.divider()

    # ── Step 1: Fetch ──
    st.markdown("#### Step 1 — Fetch Latest Papers")
    st.caption("Grabs today's papers from cs.AI, cs.LG, cs.CL, cs.CV on arxiv")

    if st.button("📥 Fetch Papers", type="primary", disabled=not ok):
        with st.spinner("Fetching papers from arxiv... (~10 seconds)"):
            try:
                result = fetch_papers()
                st.success(f"✅ {result['message']}")
            except Exception as e:
                st.error(f"❌ {e}")

    st.divider()

    # ── Step 2: Analyze ──
    st.markdown("#### Step 2 — Analyze with Llama3")
    st.caption("Runs AI on each unanalyzed paper. Takes 1-2 minutes per paper on CPU.")

    st.warning("⏳ This is slow on CPU — each paper takes 60-120 seconds. Start it and go make coffee!")

    if st.button("🤖 Analyze Papers", type="primary", disabled=not ok):
        with st.spinner("Analyzing papers with Llama3... This will take a while. Please wait and don't close the browser."):
            try:
                result = analyze_papers()
                st.success(f"✅ {result['message']}")
                st.balloons()
            except requests.exceptions.Timeout:
                st.warning("⏳ Analysis is still running in the background — the request timed out but processing continues. Wait a few minutes then check the Papers tab.")
            except Exception as e:
                st.error(f"❌ {e}")

    st.divider()

    # ── Tips ──
    st.markdown("#### 💡 Tips")
    st.markdown("""
    - **Run Fetch + Analyze once a week** to stay up to date
    - Papers are saved locally — you don't re-analyze already processed papers
    - Switch model in `backend/ai_engine.py` → change `MODEL_NAME = "llama3"` to any Ollama model
    - Check `backend/papers_db.json` to see all stored papers
    - Arxiv updates daily — new papers appear Monday to Friday
    """)

    st.divider()
    st.markdown("#### 🗑️ Reset")
    if st.button("Clear all stored papers", type="secondary"):
        try:
            import os
            for f in ["papers_db.json", "metadata.json"]:
                path = f"../backend/{f}"
                if os.path.exists(path):
                    os.remove(path)
            st.success("Cleared! Restart the backend to apply.")
        except Exception as e:
            st.error(f"Could not clear: {e}")


# ── FOOTER ────────────────────────────────────────────────────────────

st.divider()
st.markdown("""
<div style="text-align:center; color:#aaa; font-size:13px; padding:10px 0;">
    AI Research Tracker · Powered by Arxiv + Ollama Llama3 · 100% Free & Local
</div>
""", unsafe_allow_html=True)
