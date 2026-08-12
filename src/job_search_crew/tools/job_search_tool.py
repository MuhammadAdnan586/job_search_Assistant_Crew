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


class JobSearchTool(BaseTool):
    name: str = "search_jobs"
    description: str = (
        "Kisi job title aur location ke hisab se current job listings "
        "dhoondta hai. Company naam, requirements, salary (agar available "
        "ho), aur ASAL POSTING URL return karta hai. Agar real data available "
        "nahi hai, clearly 'is_demo_data' flag ke sath batata hai."
    )
    args_schema: type[BaseModel] = JobSearchInput

    def _run(self, job_title: str, location: str) -> str:
        api_key = os.getenv("SERPAPI_API_KEY")

        # ---------- REAL API VERSION (agar SERPAPI_API_KEY .env mein hai) ----------
        if api_key and api_key != "your_serpapi_key_yahan":
            try:
                import requests

                url = "https://serpapi.com/search"
                params = {
                    "engine": "google_jobs",
                    "q": f"{job_title} {location}",
                    "api_key": api_key,
                }
                response = requests.get(url, params=params, timeout=15)
                data = response.json()
                jobs = data.get("jobs_results", [])

                if not jobs:
                    return "[DEMO DATA — NOT REAL LISTINGS]\nNo real jobs found via API for this search. Falling back to demo listings below.\n" + self._dummy_data(job_title, location)

                formatted = "[REAL DATA — via SerpAPI Google Jobs]\n\n"
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
                return formatted
            except Exception as e:
                return f"[DEMO DATA — NOT REAL LISTINGS]\nReal API call failed ({e}). Falling back to demo listings below.\n" + self._dummy_data(job_title, location)

        # ---------- DUMMY VERSION (default, no API key set) ----------
        return self._dummy_data(job_title, location)

    def _dummy_data(self, job_title: str, location: str) -> str:
        return f"""[DEMO DATA — NOT REAL LISTINGS. These are placeholder examples only.
To get real, verifiable job listings with working links, add a SERPAPI_API_KEY
to your .env file (free tier available at serpapi.com).]

Job Title: {job_title} | Location: {location}

1. Company: TechNova Solutions (example)
   Requirements: Python, FastAPI, REST APIs, 1-2 years experience
   Salary: PKR 80,000 - 120,000/month
   Posting URL: https://example.com/jobs/technova-python-developer (DEMO LINK — not real)

2. Company: CloudBridge Systems (example)
   Requirements: Python, Django/FastAPI, SQL, Git
   Salary: PKR 90,000 - 140,000/month
   Posting URL: https://example.com/jobs/cloudbridge-python-developer (DEMO LINK — not real)

3. Company: DataSphere AI (example)
   Requirements: Python, Machine Learning basics, API integration
   Salary: Not disclosed
   Posting URL: https://example.com/jobs/datasphere-python-developer (DEMO LINK — not real)
"""
