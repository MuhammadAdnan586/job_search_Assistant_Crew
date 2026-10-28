# Job Search Assistant Crew

A 7-agent multi-agent system (CrewAI + Gemini) that goes from job research all the way to a
**human-reviewed application draft**, with production-grade features
(memory, guardrails, evaluation, cost tracking).

## Architecture

```
USER (job_title, location, [optional CV])
        |
        v
  Job Researcher     -> Finds jobs + posting URL (or a DEMO disclaimer)
        |                    [Guardrail: URL/demo flag required]
        v
  Job Analyzer       -> Extracts requirements/skills
        |
        v
  Resume Agent       -> REWRITES the ORIGINAL CV (full updated CV)
        |                    [Guardrail: 3 sections required]
        v
  Cover Letter Agent -> Writes a personalized cover letter from the updated CV
        |
        v
  Interview Prep     -> Provides likely questions + answer strategy
        |
        v
  Application Agent  -> Creates a complete application DRAFT (never submits)
        |                    [Guardrail: "submitted" claim forbidden]
        v
  Reviewer           -> Reviews the entire package and gives a final score
        |
        v
  Streamlit UI (tabs + human-review checkpoint + downloadable report)
```

## New Production Features (From Roadmap Phase 4)

| Feature | Where It's Implemented |
|---|---|
| **Memory (short + long-term)** | `crew.py` — `memory=True`, ChromaDB is saved locally in the `crew_memory/` folder. Short-term memory is shown in the Streamlit sidebar as session history. |
| **Guardrails** | `crew.py` — `guardrail=` functions on three tasks (research URL check, resume section check, application "no auto-submit" check). If a guardrail fails, CrewAI retries automatically. |
| **Human-in-the-loop** | `app.py` — The Application Draft tab has a checkbox; until the user confirms "I have reviewed this," no "submit" action happens. With this system, **no application is ever submitted automatically**. |
| **Evaluation** | The guardrails are themselves a form of evaluation (task success is validated before acceptance) — the expected_output of each task defines its evaluation criteria. |
| **Cost & Latency tracking** | `app.py` — The "Execution Insights" expander shows duration, token usage, and LLM call count. |
| **Observability** | `verbose=True` gives the full agent reasoning trace in the terminal; the UI shows summary metrics. |

## Tech Stack

- **CrewAI** (agents, tasks, memory, guardrails)
- **Google Gemini API** (`gemini-3.5-flash-lite`)
- **Streamlit** — UI
- **pypdf** — extracting text from a CV (PDF)
- **SerpAPI (optional)** — real, verifiable job listings + URLs

## Setup (Local)

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Add your GEMINI_API_KEY in .env
# (optional) Also add SERPAPI_API_KEY for real job listings — serpapi.com free tier
```

## Running

```bash
streamlit run app.py
```

- Enter a job title + location
- **Upload CV** checkbox — as soon as you tick it, the PDF uploader appears
  (the earlier bug is fixed — the checkbox is now outside `st.form`)
- Results appear in 7 tabs
- The **Application Draft tab** has a clear reminder: the system never applies
  on its own — it only prepares a draft, and you review it and apply yourself
  through the official job link

## Real vs Demo Job Data

If `SERPAPI_API_KEY` is not set in `.env`, the app **clearly warns you**
(orange banner) that the job listings are demo/placeholder data, not real, so
there is never any confusion that fake jobs are real. To get real, verifiable
listings (with working links), create a free SerpAPI account.

## Gemini Rate Limits

Free tier (`gemini-3.5-flash-lite`): 15 requests/minute, 500 requests/day.
The full pipeline (7 agents + memory embeddings) makes about 10-12 API calls
per run. Running it repeatedly in quick succession may hit the per-minute
limit — the UI handles this error with a friendly message.

## Pushing to GitHub

```bash
git init
git add .
git commit -m "Job Search Assistant Crew — production features"
git branch -M main
git remote add origin https://github.com/<your-username>/job-search-crew.git
git push -u origin main
```

**Important:** `.env` and `crew_memory/` (if created) will never be pushed
(they are in `.gitignore`) — keep your API keys and local memory secret.

## Deploying (Free)

**Streamlit Community Cloud:** Connect with GitHub at
[share.streamlit.io](https://share.streamlit.io), set `app.py` as the main file,
and under "Advanced settings" add `GEMINI_API_KEY` (and optionally
`SERPAPI_API_KEY`) as secrets.

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
