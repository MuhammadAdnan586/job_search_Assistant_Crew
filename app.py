"""
Job Search Assistant Crew — Streamlit UI

To run: streamlit run app.py
"""

import os
import time
import json
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from src.job_search_crew.crew import JobSearchCrew

load_dotenv()

# ---------------------------------------------------------------------------
# ENSURE DARK THEME CONFIG EXISTS (taake manually copy karna na pare)
# ---------------------------------------------------------------------------
_config_dir = Path(".streamlit")
_config_file = _config_dir / "config.toml"
if not _config_file.exists():
    _config_dir.mkdir(exist_ok=True)
    _config_file.write_text(
        "[theme]\n"
        'base = "dark"\n'
        'primaryColor = "#f2a93b"\n'
        'backgroundColor = "#0a0c10"\n'
        'secondaryBackgroundColor = "#12151b"\n'
        'textColor = "#e7eaee"\n'
        'font = "sans serif"\n'
    )

# ---------------------------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Job Search Assistant",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# FONTS — Space Grotesk (display/mono-technical headers), Inter (body),
# JetBrains Mono (agent IDs / console labels)
# ---------------------------------------------------------------------------
st.markdown(
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&'
    'family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;700&display=swap" '
    'rel="stylesheet">',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# ROBUST CUSTOM CSS — "mission control" console theme (charcoal + amber/teal)
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    :root {
        --bg: #0a0c10;
        --panel: #12151b;
        --panel-2: #171b23;
        --border: #232a36;
        --amber: #f2a93b;
        --amber-dim: #b9822f;
        --teal: #2dd6c4;
        --text: #e7eaee;
        --text-dim: #8891a1;
        --danger: #f2545b;
    }

    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: var(--bg) !important;
        color: var(--text) !important;
    }
    [data-testid="stHeader"] { background-color: transparent !important; }
    [data-testid="stSidebar"] {
        background-color: #0d1015 !important;
        border-right: 1px solid var(--border);
    }
    * { font-family: 'Inter', sans-serif; }
    h1, h2, h3, h4, h5, p, span, label, li {
        color: var(--text) !important;
    }

    /* ---------- HERO ---------- */
    .hero-eyebrow {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        letter-spacing: 0.18em;
        color: var(--teal) !important;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }
    .hero-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--text) !important;
        letter-spacing: -0.01em;
        margin-bottom: 0.3rem;
    }
    .hero-title .accent { color: var(--amber) !important; }
    .hero-sub { color: var(--text-dim) !important; font-size: 1rem; margin-bottom: 1.6rem; max-width: 640px; }

    /* ---------- PIPELINE STRIP (signature element) ---------- */
    .pipeline-wrap {
        display: flex;
        align-items: center;
        overflow-x: auto;
        gap: 0;
        padding: 1.1rem 0.2rem 1.5rem 0.2rem;
        margin-bottom: 1.6rem;
        border-bottom: 1px solid var(--border);
    }
    .pipe-node {
        display: flex;
        flex-direction: column;
        align-items: center;
        min-width: 84px;
        flex-shrink: 0;
    }
    .pipe-node .num {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem;
        color: var(--amber) !important;
        letter-spacing: 0.05em;
        margin-bottom: 0.35rem;
    }
    .pipe-node .dot {
        width: 38px; height: 38px;
        border-radius: 10px;
        background: var(--panel);
        border: 1px solid var(--border);
        display: flex; align-items: center; justify-content: center;
        font-size: 1.05rem;
        box-shadow: 0 0 0 0 rgba(242,169,59,0);
        transition: box-shadow .3s ease, border-color .3s ease;
    }
    .pipe-node:hover .dot {
        border-color: var(--amber);
        box-shadow: 0 0 14px 0 rgba(242,169,59,0.35);
    }
    .pipe-node .lbl {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.62rem;
        color: var(--text-dim) !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-top: 0.4rem;
        text-align: center;
    }
    .pipe-link {
        flex: 1;
        min-width: 18px;
        height: 1px;
        background: linear-gradient(90deg, var(--amber-dim), var(--teal));
        opacity: 0.45;
        margin: 0 2px 1.6rem 2px;
        position: relative;
        top: -0.9rem;
    }

    /* ---------- INPUTS ---------- */
    .stTextInput > div > div > input,
    .stTextArea textarea {
        background-color: var(--panel) !important;
        color: var(--text) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: var(--amber) !important;
        box-shadow: 0 0 0 1px var(--amber) !important;
    }
    label[data-testid="stWidgetLabel"] p {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.78rem !important;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        color: var(--text-dim) !important;
    }

    /* ---------- BUTTONS ---------- */
    div.stButton > button:first-child,
    div.stDownloadButton > button:first-child {
        background: var(--amber);
        color: #14161c !important;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        border-radius: 8px;
        border: none;
        padding: 0.6rem 1.4rem;
        width: 100%;
        transition: background .2s ease, transform .1s ease;
    }
    div.stButton > button:first-child:hover,
    div.stDownloadButton > button:first-child:hover {
        background: #ffc267;
        transform: translateY(-1px);
    }

    /* ---------- TABS ---------- */
    button[data-baseweb="tab"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.82rem !important;
        color: var(--text-dim) !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: var(--amber) !important;
    }
    [data-baseweb="tab-highlight"] { background-color: var(--amber) !important; }

    /* ---------- AGENT OUTPUT CARDS ---------- */
    .agent-card {
        background-color: var(--panel);
        border: 1px solid var(--border);
        border-left: 3px solid var(--teal);
        border-radius: 10px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 1rem;
        color: #dfe3e9 !important;
        line-height: 1.55;
    }
    .agent-badge {
        display: inline-block;
        font-family: 'JetBrains Mono', monospace;
        background: rgba(242,169,59,0.10);
        color: var(--amber) !important;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.72rem;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        font-weight: 600;
        margin-bottom: 0.6rem;
        border: 1px solid rgba(242,169,59,0.25);
    }

    /* ---------- BANNERS ---------- */
    .demo-banner {
        background: rgba(242, 169, 59, 0.08);
        border: 1px solid var(--amber-dim);
        color: #f2c179 !important;
        padding: 0.7rem 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        font-size: 0.9rem;
    }
    .review-banner {
        background: rgba(45, 214, 196, 0.08);
        border: 1px solid var(--teal);
        color: #8fe9de !important;
        padding: 0.9rem 1.1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        font-size: 0.92rem;
        font-weight: 600;
    }

    /* ---------- SIDEBAR HEADERS ---------- */
    [data-testid="stSidebar"] h3 {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 1rem !important;
    }

    /* ---------- METRICS ---------- */
    [data-testid="stMetricValue"] {
        font-family: 'Space Grotesk', sans-serif !important;
        color: var(--amber) !important;
    }

    .footer-note { color: #565e6b !important; font-size: 0.78rem; text-align: center; margin-top: 2.2rem; font-family: 'JetBrains Mono', monospace; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# SESSION STATE — SHORT-TERM MEMORY (this browser session's history)
# ---------------------------------------------------------------------------
if "search_history" not in st.session_state:
    st.session_state.search_history = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "application_confirmed" not in st.session_state:
    st.session_state.application_confirmed = False

# ---------------------------------------------------------------------------
# SIDEBAR — Memory (short-term) + Observability/Cost info
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🧠 Memory")
    st.caption(
        "**Short-term:** this session's history is shown below.\n\n"
        "**Long-term:** CrewAI saves past runs in the `crew_memory/` folder "
        "(local ChromaDB), so future runs benefit from richer context."
    )
    if st.session_state.search_history:
        for i, h in enumerate(reversed(st.session_state.search_history[-5:])):
            st.markdown(f"- {h}")
    else:
        st.caption("No search has been run in this session yet.")

    st.markdown("---")
    st.markdown("### 🛡️ Guardrails Active")
    st.caption(
        "✅ Research output — URL/demo-disclaimer required\n\n"
        "✅ Resume output — 3 required sections enforced\n\n"
        "✅ Application draft — cannot claim auto-submission"
    )

# ---------------------------------------------------------------------------
# AGENT PIPELINE METADATA (shared by hero strip + result tabs)
# ---------------------------------------------------------------------------
AGENTS = [
    ("01", "🔎", "Researcher"),
    ("02", "🧭", "Analyzer"),
    ("03", "📝", "Resume"),
    ("04", "✉️", "Cover Letter"),
    ("05", "🎤", "Interview"),
    ("06", "📨", "Application"),
    ("07", "✅", "Reviewer"),
]

# ---------------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------------
st.markdown('<div class="hero-eyebrow">CrewAI × Gemini · Multi-Agent Pipeline</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-title">Job Search <span class="accent">Assistant</span></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-sub">Seven agents run in sequence — from live research to a '
    'human-reviewed application draft. Nothing is ever auto-submitted.</div>',
    unsafe_allow_html=True,
)

pipeline_html = '<div class="pipeline-wrap">'
for i, (num, icon, label) in enumerate(AGENTS):
    pipeline_html += (
        f'<div class="pipe-node"><span class="num">{num}</span>'
        f'<div class="dot">{icon}</div><span class="lbl">{label}</span></div>'
    )
    if i < len(AGENTS) - 1:
        pipeline_html += '<div class="pipe-link"></div>'
pipeline_html += '</div>'
st.markdown(pipeline_html, unsafe_allow_html=True)

if not os.getenv("SERPAPI_API_KEY") or os.getenv("SERPAPI_API_KEY") == "your_serpapi_key_yahan":
    st.markdown(
        '<div class="demo-banner">⚠️ Real job search API (SERPAPI_API_KEY) is not configured — '
        'job listings will be DEMO/placeholder data, not real. Add a key to the .env file from '
        '<a href="https://serpapi.com" style="color:#fbbf24;">serpapi.com</a> for a free tier.</div>',
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# HELPER: extract text from uploaded PDF CV
# ---------------------------------------------------------------------------
def extract_cv_text(uploaded_file) -> str:
    try:
        from pypdf import PdfReader
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# INPUT SECTION (NO st.form — taake checkbox turant UI update kare)
# ---------------------------------------------------------------------------
col1, col2 = st.columns(2)
with col1:
    job_title = st.text_input("Job Title", placeholder="e.g. Python Developer")
with col2:
    location = st.text_input("Location", placeholder="e.g. Rawalpindi, Pakistan")

with st.expander("🎚️ Filters (optional)"):
    fcol1, fcol2 = st.columns(2)
    with fcol1:
        job_type = st.selectbox(
            "Job Type", ["Any", "Full-time", "Part-time", "Internship", "Contract"]
        )
        experience_level = st.selectbox(
            "Experience Level", ["Any", "Entry Level", "Mid Level", "Senior Level"]
        )
        posted_date = st.selectbox(
            "Posted Date", ["Any time", "Past 24 hours", "Past week", "Past month"]
        )
    with fcol2:
        remote_type = st.selectbox("Work Mode", ["Any", "Remote", "Onsite", "Hybrid"])
        salary_range = st.text_input(
            "Salary Range (optional)", placeholder="e.g. PKR 80,000 - 150,000"
        )

_filter_badges = []
if job_type != "Any":
    _filter_badges.append(f"Job Type: {job_type}")
if remote_type != "Any":
    _filter_badges.append(f"Work Mode: {remote_type}")
if experience_level != "Any":
    _filter_badges.append(f"Experience: {experience_level}")
if salary_range.strip():
    _filter_badges.append(f"Salary: {salary_range.strip()}")
if posted_date != "Any time":
    _filter_badges.append(f"Posted: {posted_date}")

filters_text = "; ".join(_filter_badges) if _filter_badges else "No specific filters applied"

if _filter_badges:
    badges_html = "".join(f'<span class="agent-badge" style="margin-right:6px;">{b}</span>' for b in _filter_badges)
    st.markdown(f'<div style="margin-bottom:0.8rem;">{badges_html}</div>', unsafe_allow_html=True)

use_cv = st.checkbox(
    "📄 Upload your CV to personalize the results",
    value=False,
    help="Uploading a CV means the Resume, Cover Letter, Interview Prep, and Application Draft will be based on your actual background.",
)

uploaded_cv = None
if use_cv:
    uploaded_cv = st.file_uploader("Upload CV (PDF)", type=["pdf"], key="cv_uploader")
    if uploaded_cv:
        st.success(f"✅ '{uploaded_cv.name}' uploaded — click the button below to start the search.")
else:
    st.caption("No CV uploaded — you'll get general results based only on job title/location.")

run_clicked = st.button("🚀 Search & Generate Package")

# ---------------------------------------------------------------------------
# RUN PIPELINE
# ---------------------------------------------------------------------------
if run_clicked:
    if not job_title or not location:
        st.error("Job title and location are both required.")
        st.stop()
    if use_cv and uploaded_cv is None:
        st.error("You selected the CV upload option — please upload a PDF first.")
        st.stop()

    user_background = ""
    if use_cv:
        with st.spinner("Extracting information from your CV..."):
            user_background = extract_cv_text(uploaded_cv)
        if not user_background:
            st.warning("Couldn't extract text from the CV — generating general results instead.")
            user_background = f"Candidate applying for {job_title} role."
    else:
        user_background = f"Candidate applying for {job_title} role in {location}. No CV provided — general profile."

    inputs = {
        "job_title": job_title,
        "location": location,
        "user_background": user_background,
        "filters_text": filters_text,
    }

    status_placeholder = st.empty()
    progress = st.progress(5, text="Starting the Job Researcher...")

    try:
        status_placeholder.info("⏳ Pipeline running — 7 agents are working, this will take a moment...")
        start_time = time.time()

        crew_output = JobSearchCrew().crew().kickoff(inputs=inputs)

        duration = round(time.time() - start_time, 1)
        progress.progress(100, text="Complete!")
        status_placeholder.success(f"✅ Your full package is ready! ({duration}s)")

        st.session_state.search_history.append(
            f"{job_title} — {location}" + (f" ({filters_text})" if _filter_badges else "")
        )
        st.session_state.application_confirmed = False

        task_outputs = getattr(crew_output, "tasks_output", None)
        labels = [
            "research", "analysis", "resume", "cover_letter",
            "interview_prep", "application", "review",
        ]
        contents = {}
        if task_outputs and len(task_outputs) >= 7:
            for label, t in zip(labels, task_outputs):
                contents[label] = t.raw
        else:
            contents = {label: "" for label in labels}
            contents["review"] = str(crew_output)

        token_usage = getattr(crew_output, "token_usage", None)

        st.session_state.last_result = {
            "contents": contents,
            "job_title": job_title,
            "duration": duration,
            "token_usage": token_usage,
        }

    except Exception as e:
        error_msg = str(e)
        progress.empty()
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
            status_placeholder.error(
                "⏱️ The Gemini API free-tier limit has been exceeded right now. "
                "Please wait a few minutes and try again."
            )
        else:
            status_placeholder.error(f"❌ Something went wrong: {error_msg}")

# ---------------------------------------------------------------------------
# DISPLAY RESULTS (agar available hon)
# ---------------------------------------------------------------------------
result = st.session_state.last_result
if result:
    contents = result["contents"]

    tab_labels = [
        "🔎 Research", "🧭 Analysis", "📝 Resume (Before/After)",
        "✉️ Cover Letter", "🎤 Interview Prep", "📨 Application Draft", "✅ Final Review",
    ]
    keys = ["research", "analysis", "resume", "cover_letter", "interview_prep", "application", "review"]
    tabs = st.tabs(tab_labels)

    for tab, label, key in zip(tabs, tab_labels, keys):
        with tab:
            st.markdown(f'<span class="agent-badge">{label}</span>', unsafe_allow_html=True)

            if key == "application":
                st.markdown(
                    '<div class="review-banner">🧑‍💻 HUMAN-IN-THE-LOOP CHECKPOINT: '
                    'This is a DRAFT. No application has been submitted automatically. '
                    'Review every detail below carefully, fill in your contact details, '
                    'and apply yourself via the official job link.</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(f'<div class="agent-card">{contents[key]}</div>', unsafe_allow_html=True)
                st.session_state.application_confirmed = st.checkbox(
                    "✅ I have carefully reviewed the full application draft and "
                    "am ready to submit it myself",
                    value=st.session_state.application_confirmed,
                )
                if st.session_state.application_confirmed:
                    st.success("Confirmed — you can now go to the official job link and apply yourself.")
            else:
                st.markdown(f'<div class="agent-card">{contents[key]}</div>', unsafe_allow_html=True)

    # -------------------------------------------------------------
    # OBSERVABILITY + COST/LATENCY PANEL
    # -------------------------------------------------------------
    with st.expander("📊 Execution Insights (Observability, Cost & Latency)"):
        c1, c2, c3 = st.columns(3)
        c1.metric("Duration", f"{result['duration']}s")
        tu = result.get("token_usage")
        if tu:
            total_tokens = getattr(tu, "total_tokens", None) or (tu.get("total_tokens") if isinstance(tu, dict) else None)
            requests_count = getattr(tu, "successful_requests", None) or (tu.get("successful_requests") if isinstance(tu, dict) else None)
            c2.metric("Total Tokens", total_tokens if total_tokens else "N/A")
            c3.metric("LLM Calls", requests_count if requests_count else "N/A")
        else:
            c2.metric("Total Tokens", "N/A")
            c3.metric("LLM Calls", "N/A")
        st.caption(
            "These metrics are used for Cost & Latency Optimization in production — "
            "fewer tokens/calls means lower cost. A detailed step-by-step trace is "
            "already visible in the terminal thanks to verbose=True (Observability)."
        )

    # -------------------------------------------------------------
    # DOWNLOAD BUTTON
    # -------------------------------------------------------------
    full_text = "\n\n---\n\n".join(f"# {k.upper()}\n\n{v}" for k, v in contents.items())
    st.download_button(
        "⬇️ Download Full Package (.md)",
        data=full_text,
        file_name=f"{result['job_title'].replace(' ', '_')}_application_package.md",
        mime="text/markdown",
    )

st.markdown(
    '<div class="footer-note">Built with CrewAI + Gemini · Job Search Assistant · '
    'Applications are NEVER auto-submitted — human review always required.</div>',
    unsafe_allow_html=True,
)