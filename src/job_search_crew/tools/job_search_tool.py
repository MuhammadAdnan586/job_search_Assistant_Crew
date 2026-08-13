"""
Ye tool Job Researcher agent use karega jobs dhoondne ke liye.

Concept Yaad Rakhein: Ye bilkul wahi 'get_weather' wala concept hai jo humne
Week 9 mein AI Studio pe try kiya tha — ek function jise LLM khud call karne
ka faisla karta hai, jab usay lagta hai ke isse kaam hoga.

Zaroori Baat: Agar .env mein SERPAPI_API_KEY nahi hai, ye tool DUMMY data
deta hai — lekin har dummy result mein ek clear "is_demo_data: true" flag
hota hai, taake agent (aur is se aage user) ko pata rahe ke ye REAL job
listings nahi hain. Ye honest-by-design approach hai — kabhi bhi fake data
ko "real" hone ka bhram nahi dena chahiye.
"""

import os
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class JobSearchInput(BaseModel):
    """Tool ke input parameters ka schema."""
    job_title: str = Field(..., description="Jis job ki talash hai, jaise 'Python Developer'")
    location: str = Field(..., description="Job ki location, jaise 'Rawalpindi' ya 'Remote'")
    job_type: str = Field(
        default="Any",
        description="Employment type filter: 'Any', 'Full-time', 'Part-time', 'Internship', or 'Contract'.",
    )
    remote_type: str = Field(
        default="Any",
        description="Work mode filter: 'Any', 'Remote', 'Onsite', or 'Hybrid'.",
    )
    experience_level: str = Field(
        default="Any",
        description="Experience level filter: 'Any', 'Entry Level', 'Mid Level', or 'Senior Level'.",
    )
    salary_range: str = Field(
        default="",
        description="Desired salary range as free text, e.g. 'PKR 80,000 - 150,000'. Leave empty if none.",
    )
    posted_date: str = Field(
        default="Any time",
        description="How recent the listing should be: 'Any time', 'Past 24 hours', 'Past week', or 'Past month'.",
    )


class JobSearchTool(BaseTool):
    name: str = "search_jobs"
    description: str = (
        "Kisi job title aur location ke hisab se current job listings "
        "dhoondta hai. Optional filters bhi accept karta hai: job_type, "
        "remote_type, experience_level, salary_range, aur posted_date. "
        "Company naam, requirements, salary (agar available ho), aur ASAL "
        "POSTING URL return karta hai. Agar real data available nahi hai, "
        "clearly 'is_demo_data' flag ke sath batata hai."
    )
    args_schema: type[BaseModel] = JobSearchInput

    def _run(
        self,
        job_title: str,
        location: str,
        job_type: str = "Any",
        remote_type: str = "Any",
        experience_level: str = "Any",
        salary_range: str = "",
        posted_date: str = "Any time",
    ) -> str:
        api_key = os.getenv("SERPAPI_API_KEY")
        filters = {
            "job_type": job_type,
            "remote_type": remote_type,
            "experience_level": experience_level,
            "salary_range": salary_range,
            "posted_date": posted_date,
        }

        # Query text ko relevant filter-words se enrich karo (Google Jobs
        # natural-language matching in inko achay se samajh leta hai).
        # NOTE: SerpAPI Google Jobs ka "chips" param sirf un exact/hashed
        # values ko accept karta hai jo khud API pehle response mein deta
        # hai — free-text guess (jaise "employment_type:FULLTIME") bhejne se
        # request fail ho jati hai aur silently demo data pe fallback ho
        # jata hai. Isliye hum filters ko chips ki bajaye search query mein
        # natural keywords ki tarah shamil karte hain — ye zyada reliable hai.
        query_parts = [job_title, location]
        if job_type and job_type != "Any":
            query_parts.append(job_type)
        if remote_type and remote_type != "Any":
            query_parts.append(remote_type)
        if experience_level and experience_level != "Any":
            query_parts.append(experience_level)
        query = " ".join(query_parts)

        # ---------- REAL API VERSION (agar SERPAPI_API_KEY .env mein hai) ----------
        if api_key and api_key != "your_serpapi_key_yahan":
            try:
                import requests

                url = "https://serpapi.com/search"

                def _fetch(q: str):
                    params = {"engine": "google_jobs", "q": q, "api_key": api_key}
                    resp = requests.get(url, params=params, timeout=15)
                    data = resp.json()
                    print(f"[JobSearchTool DEBUG] query='{q}' | status={resp.status_code} | "
                          f"error={data.get('error')} | jobs_found={len(data.get('jobs_results', []))}")
                    return data.get("jobs_results", [])

                print(f"[JobSearchTool DEBUG] filters received: job_type={job_type!r}, "
                      f"remote_type={remote_type!r}, experience_level={experience_level!r}, "
                      f"posted_date={posted_date!r}, salary_range={salary_range!r}")

                jobs = _fetch(query)
                used_fallback_query = False

                # Agar filters ke sath query bohot narrow ho gayi aur kuch na
                # mila, to plain query (sirf job_title + location) try karo —
                # taake real data milne ke chances barhen filters ke bawajood.
                base_query = f"{job_title} {location}"
                if not jobs and query != base_query:
                    jobs = _fetch(base_query)
                    used_fallback_query = True

                if not jobs:
                    return (
                        "[DEMO DATA — NOT REAL LISTINGS]\nNo real jobs found via API "
                        "for this search (even without filters). Falling back to demo "
                        "listings below.\n" + self._dummy_data(job_title, location, filters)
                    )

                formatted = f"[REAL DATA — via SerpAPI Google Jobs]\nFilters applied (as search keywords): {self._filters_summary(filters)}\n\n"
                if used_fallback_query:
                    formatted += (
                        "Note: filtered search returned no results, so these results are "
                        "from a broader search without the filter keywords — please check "
                        "each listing manually against your filters.\n\n"
                    )
                for i, job in enumerate(jobs[:5], start=1):
                    apply_link = ""
                    apply_options = job.get("apply_options", [])
                    if apply_options:
                        apply_link = apply_options[0].get("link", "Not available")
                    formatted += (
                        f"{i}. Company: {job.get('company_name', 'N/A')}\n"
                        f"   Title: {job.get('title', 'N/A')}\n"
                        f"   Location: {job.get('location', 'N/A')}\n"
                        f"   Description snippet: {job.get('description', '')[:200]}\n"
                        f"   Posting URL: {apply_link}\n\n"
                    )
                notes = []
                if salary_range.strip():
                    notes.append(
                        f"user requested salary range '{salary_range.strip()}' — "
                        "Google Jobs does not always expose salary data, verify on the posting page itself"
                    )
                if posted_date and posted_date != "Any time":
                    notes.append(
                        f"user requested posted-date filter '{posted_date}' — this search source does not "
                        "reliably support strict date filtering, so check each posting's date manually"
                    )
                if notes:
                    formatted += "Note: " + "; ".join(notes) + ".\n"
                return formatted
            except Exception as e:
                print(f"[JobSearchTool DEBUG] EXCEPTION: {type(e).__name__}: {e}")
                return (
                    f"[DEMO DATA — NOT REAL LISTINGS]\nReal API call failed ({e}). "
                    "Falling back to demo listings below.\n"
                    + self._dummy_data(job_title, location, filters)
                )

        # ---------- DUMMY VERSION (default, no API key set) ----------
        return self._dummy_data(job_title, location, filters)

    def _filters_summary(self, filters: dict) -> str:
        parts = []
        if filters["job_type"] != "Any":
            parts.append(f"Job Type={filters['job_type']}")
        if filters["remote_type"] != "Any":
            parts.append(f"Work Mode={filters['remote_type']}")
        if filters["experience_level"] != "Any":
            parts.append(f"Experience={filters['experience_level']}")
        if filters["salary_range"].strip():
            parts.append(f"Salary={filters['salary_range'].strip()}")
        if filters["posted_date"] != "Any time":
            parts.append(f"Posted={filters['posted_date']}")
        return "; ".join(parts) if parts else "None"

    def _dummy_data(self, job_title: str, location: str, filters: dict = None) -> str:
        filters = filters or {}
        filters_line = f"Filters applied (demo/simulated): {self._filters_summary(filters)}\n" if filters else ""
        job_type_note = filters.get("job_type", "Any")
        remote_note = filters.get("remote_type", "Any")
        exp_note = filters.get("experience_level", "Any")
        return f"""[DEMO DATA — NOT REAL LISTINGS. These are placeholder examples only.
To get real, verifiable job listings with working links, add a SERPAPI_API_KEY
to your .env file (free tier available at serpapi.com).]

Job Title: {job_title} | Location: {location}
{filters_line}
1. Company: TechNova Solutions (example)
   Employment Type: {job_type_note if job_type_note != "Any" else "Full-time"} | Work Mode: {remote_note if remote_note != "Any" else "Onsite"}
   Requirements: Python, FastAPI, REST APIs, {exp_note if exp_note != "Any" else "1-2 years"} experience
   Salary: PKR 80,000 - 120,000/month
   Posting URL: https://example.com/jobs/technova-python-developer (DEMO LINK — not real)

2. Company: CloudBridge Systems (example)
   Employment Type: {job_type_note if job_type_note != "Any" else "Full-time"} | Work Mode: {remote_note if remote_note != "Any" else "Remote"}
   Requirements: Python, Django/FastAPI, SQL, Git
   Salary: PKR 90,000 - 140,000/month
   Posting URL: https://example.com/jobs/cloudbridge-python-developer (DEMO LINK — not real)

3. Company: DataSphere AI (example)
   Employment Type: {job_type_note if job_type_note != "Any" else "Contract"} | Work Mode: {remote_note if remote_note != "Any" else "Hybrid"}
   Requirements: Python, Machine Learning basics, API integration
   Salary: Not disclosed
   Posting URL: https://example.com/jobs/datasphere-python-developer (DEMO LINK — not real)
"""