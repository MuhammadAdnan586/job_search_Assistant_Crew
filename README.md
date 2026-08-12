# Job Search Assistant Crew

Ek 7-agent multi-agent system (CrewAI + Gemini) — job research se lekar ek
**human-reviewed application draft** tak, production-grade features
(memory, guardrails, evaluation, cost tracking) ke sath.

## Architecture

```
USER (job_title, location, [optional CV])
        |
        v
  Job Researcher    -> Jobs dhoondta hai + posting URL (ya DEMO disclaimer)
        |                    [Guardrail: URL/demo-flag required]
        v
  Job Analyzer      -> Requirements/skills nikaalta hai
        |
        v
  Resume Agent      -> ORIGINAL CV ko REWRITE karta hai (poora updated CV)
        |                    [Guardrail: 3 sections required]
        v
  Cover Letter Agent -> Updated CV se personalized cover letter likhta hai
        |
        v
  Interview Prep    -> Likely questions + answer strategy deta hai
        |
        v
  Application Agent -> Complete application DRAFT banata hai (kabhi submit nahi karta)
        |                    [Guardrail: "submitted" claim forbidden]
        v
  Reviewer          -> Poori package review karta hai, final score deta hai
        |
        v
  Streamlit UI (tabs + human-review checkpoint + downloadable report)
```

## Naye Production Features (Roadmap Phase 4 Se)

| Feature | Kahan Implement Hai |
|---|---|
| **Memory (short + long-term)** | `crew.py` — `memory=True`, ChromaDB `crew_memory/` folder mein local save hota hai. Short-term Streamlit sidebar mein session history ke tor pe dikhta hai. |
| **Guardrails** | `crew.py` — teen tasks pe `guardrail=` functions (research URL check, resume section check, application "no auto-submit" check). Fail hone pe CrewAI khud retry karta hai. |
| **Human-in-the-loop** | `app.py` — Application Draft tab mein checkbox jab tak user khud confirm na kare "maine review kar li," aage koi "submit" action nahi hota — is system se **koi application kabhi automatically submit nahi hoti**. |
| **Evaluation** | Guardrails khud ek evaluation form hain (task success validated before acceptance) — expected_output har task mein evaluation criteria define karta hai. |
| **Cost & Latency tracking** | `app.py` — "Execution Insights" expander mein duration, token usage, LLM call count dikhta hai. |
| **Observability** | Terminal mein `verbose=True` se poora agent reasoning trace milta hai; UI mein summary metrics. |

## Tech Stack

- **CrewAI** (agents, tasks, memory, guardrails)
- **Google Gemini API** (`gemini-3.5-flash-lite`)
- **Streamlit** — UI
- **pypdf** — CV (PDF) se text extract karna
- **SerpAPI (optional)** — real, verifiable job listings + URLs

## Setup (Local)

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# .env mein apni GEMINI_API_KEY daalein
# (optional) real job listings ke liye SERPAPI_API_KEY bhi daalein — serpapi.com free tier
```

## Run Karna

```bash
streamlit run app.py
```

- Job title + location daalein
- **CV upload** checkbox — tick karte hi turant PDF uploader dikhega (pehle
  wala bug fix ho gaya — checkbox ab `st.form` ke bahar hai)
- Results 7 tabs mein aayenge
- **Application Draft tab** mein ek clear reminder hai: system kabhi khud
  apply nahi karta — sirf draft taiyar karta hai, aap khud review kar ke
  official job link pe jakar apply karte hain

## Real vs Demo Job Data

Agar `.env` mein `SERPAPI_API_KEY` nahi hai, app **clearly warn karta hai**
(orange banner) ke job listings demo/placeholder hain, real nahi — taake
kabhi bhi galat fehmi na ho ke fake jobs real hain. Real, verifiable
listings (working links ke sath) ke liye SerpAPI free tier account banayein.

## Gemini Rate Limits

Free tier (`gemini-3.5-flash-lite`): 15 requests/minute, 500 requests/day.
Poori pipeline (7 agents + memory embeddings) ek run mein ~10-12 API calls
karti hai. Turant baar-baar run karne se per-minute limit hit ho sakti hai —
UI is error ko friendly message ke sath handle karta hai.

## GitHub Pe Push Karna

```bash
git init
git add .
git commit -m "Job Search Assistant Crew — production features"
git branch -M main
git remote add origin https://github.com/<aapka-username>/job-search-crew.git
git push -u origin main
```

**Zaroori:** `.env` aur `crew_memory/` (agar ban jaye) kabhi push nahi
honge (`.gitignore` mein hain) — API keys aur local memory secret rakhein.

## Deploy Karna (Free)

**Streamlit Community Cloud:** [share.streamlit.io](https://share.streamlit.io)
pe GitHub se connect karein, main file `app.py` batayein, "Advanced settings"
mein `GEMINI_API_KEY` (aur optional `SERPAPI_API_KEY`) secrets ke tor pe
add karein.

## Folder Structure

```
job_search_crew/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── main.py                     <- CLI entry point
├── app.py                      <- Streamlit UI
└── src/job_search_crew/
    ├── crew.py                  <- Agents, tasks, memory, guardrails
    ├── config/
    │   ├── agents.yaml           <- 7 agents (English-only enforced)
    │   └── tasks.yaml            <- 7 tasks (URLs, CV rewrite, app draft)
    └── tools/
        └── job_search_tool.py    <- Real (SerpAPI) + honest demo fallback
```
