"""
Job Search Assistant Crew — Streamlit UI

Run karne ke liye: streamlit run app.py
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
        'primaryColor = "#6366f1"\n'
        'backgroundColor = "#0f1116"\n'
        'secondaryBackgroundColor = "#1a1d27"\n'
        'textColor = "#f3f4f6"\n'
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
# ROBUST CUSTOM CSS — force dark look regardless of theme file being picked up
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #0f1116 !important;
        color: #f3f4f6 !important;
    }
    [data-testid="stSidebar"] {
        background-color: #14161f !important;
    }
    h1, h2, h3, h4, h5, p, span, label, li {
        color: #f3f4f6 !important;
    }

    .hero-title {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(90deg, #6366f1, #22d3ee);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .hero-sub { color: #9ca3af !important; font-size: 1.05rem; margin-bottom: 1.5rem; }

    .stTextInput > div > div > input,
    .stTextArea textarea {
        background-color: #1a1d27 !important;
        color: #f3f4f6 !important;
        border: 1px solid #2d3142 !important;
        border-radius: 8px !important;
    }

    div.stButton > button:first-child,
    div.stDownloadButton > button:first-child {
        background: linear-gradient(90deg, #6366f1, #4f46e5);
        color: white !important;
        font-weight: 600;
        border-radius: 8px;
        border: none;
        padding: 0.6rem 1.4rem;
        width: 100%;
    }
    div.stButton > button:first-child:hover {
        background: linear-gradient(90deg, #4f46e5, #4338ca);
    }

    .agent-card {
        background-color: #1a1d27;
        border: 1px solid #2d3142;
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 1rem;
        color: #e5e7eb !important;
    }
    .agent-badge {
        display: inline-block;
        background: rgba(99,102,241,0.15);
        color: #a5b4fc !important;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-bottom: 0.6rem;
    }
    .demo-banner {
        background: rgba(245, 158, 11, 0.12);
        border: 1px solid #f59e0b;
        color: #fbbf24 !important;
        padding: 0.7rem 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        font-size: 0.9rem;
    }
    .review-banner {
        background: rgba(34, 197, 94, 0.10);
        border: 1px solid #22c55e;
        color: #86efac !important;
        padding: 0.9rem 1.1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        font-size: 0.92rem;
        font-weight: 600;
    }
    .footer-note { color: #6b7280 !important; font-size: 0.8rem; text-align: center; margin-top: 2rem; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# SESSION STATE — SHORT-TERM MEMORY (isi browser session ki history)
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
        "**Short-term:** isi session ki history neeche dikh rahi hai.\n\n"
        "**Long-term:** CrewAI purane runs ko `crew_memory/` folder mein "
        "(local ChromaDB) save karta hai, taake future runs behtar context "
        "ke sath chalein."
    )
    if st.session_state.search_history:
        for i, h in enumerate(reversed(st.session_state.search_history[-5:])):
            st.markdown(f"- {h}")
    else:
        st.caption("Abhi tak koi search nahi hui is session mein.")

    st.markdown("---")
    st.markdown("### 🛡️ Guardrails Active")
    st.caption(
        "✅ Research output — URL/demo-disclaimer required\n\n"
        "✅ Resume output — 3 required sections enforced\n\n"
        "✅ Application draft — cannot claim auto-submission"
    )

# ---------------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------------
st.markdown('<div class="hero-title">🎯 Job Search Assistant</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-sub">7 AI agents — Research, Analysis, Resume Rewrite, Cover Letter, '
    'Interview Prep, Application Draft aur Review — ek click mein. All outputs in English.</div>',
    unsafe_allow_html=True,
)

if not os.getenv("SERPAPI_API_KEY") or os.getenv("SERPAPI_API_KEY") == "your_serpapi_key_yahan":
    st.markdown(
        '<div class="demo-banner">⚠️ Real job search API (SERPAPI_API_KEY) configured nahi hai — '
        'job listings DEMO/placeholder data honge, real nahi. .env file mein key add karein '
        '<a href="https://serpapi.com" style="color:#fbbf24;">serpapi.com</a> se free tier ke liye.</div>',
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

use_cv = st.checkbox(
    "📄 Apni CV upload karke results personalize karein",
    value=False,
    help="CV upload karne se Resume, Cover Letter, Interview Prep, aur Application Draft aapke asal background pe based honge.",
)

uploaded_cv = None
if use_cv:
    uploaded_cv = st.file_uploader("CV Upload Karein (PDF)", type=["pdf"], key="cv_uploader")
    if uploaded_cv:
        st.success(f"✅ '{uploaded_cv.name}' uploaded — search shuru karne ke liye neeche button dabayein.")
else:
    st.caption("CV upload nahi ki — sirf job title/location ke hisab se general results milenge.")

run_clicked = st.button("🚀 Search & Generate Package")

# ---------------------------------------------------------------------------
# RUN PIPELINE
# ---------------------------------------------------------------------------
if run_clicked:
    if not job_title or not location:
        st.error("Job title aur location dono zaroori hain.")
        st.stop()
    if use_cv and uploaded_cv is None:
        st.error("Aapne CV upload karne ka option chuna hai — pehle PDF upload karein.")
        st.stop()

    user_background = ""
    if use_cv:
        with st.spinner("CV se information nikali ja rahi hai..."):
            user_background = extract_cv_text(uploaded_cv)
        if not user_background:
            st.warning("CV se text nahi nikal saka — general results generate ho rahe hain.")
            user_background = f"Candidate applying for {job_title} role."
    else:
        user_background = f"Candidate applying for {job_title} role in {location}. No CV provided — general profile."

    inputs = {"job_title": job_title, "location": location, "user_background": user_background}

    status_placeholder = st.empty()
    progress = st.progress(5, text="Job Researcher shuru ho raha hai...")

    try:
        status_placeholder.info("⏳ Pipeline chal rahi hai — 7 agents kaam kar rahe hain, thoda waqt lagega...")
        start_time = time.time()

        crew_output = JobSearchCrew().crew().kickoff(inputs=inputs)

        duration = round(time.time() - start_time, 1)
        progress.progress(100, text="Mukammal ho gaya!")
        status_placeholder.success(f"✅ Poora package tayyar hai! ({duration}s)")

        st.session_state.search_history.append(f"{job_title} — {location}")
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
                "⏱️ Gemini API ki free-tier limit is waqt exceed ho gayi hai. "
                "Kuch minute wait karke dobara try karein."
            )
        else:
            status_placeholder.error(f"❌ Kuch masla hua: {error_msg}")

# ---------------------------------------------------------------------------
# DISPLAY RESULTS (agar available hon)
# ---------------------------------------------------------------------------
result = st.session_state.last_result
if result:
    contents = result["contents"]

    tab_labels = [
        "🔍 Research", "🧠 Analysis", "📝 Resume (Before/After)",
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
                    'Ye ek DRAFT hai. Koi bhi application automatically submit NAHI hui. '
                    'Neeche poori detail dhyan se check karein, apni contact details fill '
                    'karein, aur khud official job link pe jakar apply karein.</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(f'<div class="agent-card">{contents[key]}</div>', unsafe_allow_html=True)
                st.session_state.application_confirmed = st.checkbox(
                    "✅ Maine poori application draft carefully review kar li hai aur "
                    "khud submit karne ke liye ready hoon",
                    value=st.session_state.application_confirmed,
                )
                if st.session_state.application_confirmed:
                    st.success("Confirmed — ab aap official job link pe jakar khud apply kar sakte hain.")
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
            "Ye metrics production mein Cost & Latency Optimization ke liye use hoti hain — "
            "jitne kam tokens/calls, utni kam cost. Detailed step-by-step trace terminal mein "
            "verbose=True ki wajah se already dikh raha hai (Observability)."
        )

    # -------------------------------------------------------------
    # DOWNLOAD BUTTON
    # -------------------------------------------------------------
    full_text = "\n\n---\n\n".join(f"# {k.upper()}\n\n{v}" for k, v in contents.items())
    st.download_button(
        "⬇️ Poora Package Download Karein (.md)",
        data=full_text,
        file_name=f"{result['job_title'].replace(' ', '_')}_application_package.md",
        mime="text/markdown",
    )

st.markdown(
    '<div class="footer-note">Built with CrewAI + Gemini · Job Search Assistant · '
    'Applications are NEVER auto-submitted — human review always required.</div>',
    unsafe_allow_html=True,
)
