"""
Ye file poore pipeline ko combine karti hai:
Job Researcher -> Job Analyzer -> Resume Agent (CV rewrite) -> Cover Letter
-> Interview Prep -> Application Draft -> Reviewer

Naye Concepts Is File Mein (jo aaj seekhe):

1. MEMORY: `memory=True` — CrewAI ko short-term (isi run ki context) aur
   long-term (purane runs se seekha hua, disk pe ChromaDB mein save hota
   hai) memory deta hai. Isse agent baar baar "bhoolta" nahi.

2. GUARDRAILS: Har zaroori Task pe `guardrail=` function laga hai — ye
   agent ke output ko accept karne se PEHLE check karta hai (jaise "kya
   research task mein URL diya gaya?"). Agar check fail ho, CrewAI khud
   agent ko dobara try karne ko kehta hai (retry logic).
"""

import os
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.tasks.task_output import TaskOutput
from dotenv import load_dotenv

from src.job_search_crew.tools.job_search_tool import JobSearchTool

load_dotenv()


# ---------------------------------------------------------------------------
# GUARDRAIL FUNCTIONS
# Har function (bool, str_or_output) return karta hai — True = accept karo,
# False = agent ko dobara try karne do (reason ke sath).
# ---------------------------------------------------------------------------

def research_output_guardrail(output: TaskOutput):
    """Confirm karta hai ke research task mein posting URL/link zaroor ho,
    aur demo-data ho to clearly mark ho."""
    text = output.raw.lower()
    if "http" not in text and "demo" not in text:
        return (False, "Output mein koi posting URL ya demo-data disclaimer nahi mila. Please include a URL for each listing, or clearly mark as DEMO DATA.")
    return (True, output.raw)


def resume_output_guardrail(output: TaskOutput):
    """Confirm karta hai ke resume task ke teeno required sections maujood hain."""
    text = output.raw
    required_sections = ["ORIGINAL CV SUMMARY", "CHANGES MADE", "UPDATED CV"]
    missing = [s for s in required_sections if s not in text]
    if missing:
        return (False, f"Missing required sections: {', '.join(missing)}. Please include all three sections exactly as instructed.")
    return (True, output.raw)


def application_output_guardrail(output: TaskOutput):
    """Confirm karta hai ke application draft mein 'submit' khud claim nahi
    ki gayi — human-in-the-loop safety check."""
    text = output.raw.lower()
    forbidden_claims = ["application has been submitted", "i have submitted", "successfully submitted"]
    if any(claim in text for claim in forbidden_claims):
        return (False, "Output incorrectly claims the application was submitted. This system must NEVER claim to submit on the user's behalf — only prepare a draft for human review.")
    if "draft" not in text.lower():
        return (False, "Output should clearly be marked as a DRAFT requiring human review before submission.")
    return (True, output.raw)


@CrewBase
class JobSearchCrew:
    """Job Search Assistant Crew — agents jo mil kar poori job
    application package taiyar karte hain (draft only, submission nahi)."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self):
        self.llm = LLM(
            model="gemini/gemini-3.5-flash-lite",
            api_key=os.getenv("GEMINI_API_KEY"),
        )

    # ---------------- AGENTS ----------------

    @agent
    def job_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["job_researcher"],
            tools=[JobSearchTool()],
            llm=self.llm,
            verbose=True,
        )

    @agent
    def job_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config["job_analyzer"],
            llm=self.llm,
            verbose=True,
        )

    @agent
    def resume_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["resume_agent"],
            llm=self.llm,
            verbose=True,
        )

    @agent
    def cover_letter_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["cover_letter_agent"],
            llm=self.llm,
            verbose=True,
        )

    @agent
    def interview_prep_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["interview_prep_agent"],
            llm=self.llm,
            verbose=True,
        )

    @agent
    def application_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["application_agent"],
            llm=self.llm,
            verbose=True,
        )

    @agent
    def reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config["reviewer"],
            llm=self.llm,
            verbose=True,
        )

    # ---------------- TASKS ----------------

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config["research_task"],
            guardrail=research_output_guardrail,
        )

    @task
    def analysis_task(self) -> Task:
        return Task(config=self.tasks_config["analysis_task"])

    @task
    def resume_task(self) -> Task:
        return Task(
            config=self.tasks_config["resume_task"],
            guardrail=resume_output_guardrail,
        )

    @task
    def cover_letter_task(self) -> Task:
        return Task(config=self.tasks_config["cover_letter_task"])

    @task
    def interview_prep_task(self) -> Task:
        return Task(config=self.tasks_config["interview_prep_task"])

    @task
    def application_task(self) -> Task:
        return Task(
            config=self.tasks_config["application_task"],
            guardrail=application_output_guardrail,
        )

    @task
    def review_task(self) -> Task:
        return Task(
            config=self.tasks_config["review_task"],
            output_file="output/final_report.md",
        )

    # ---------------- CREW ----------------

    @crew
    def crew(self) -> Crew:
        """Poori Crew assemble karta hai.

        memory=True: CrewAI ko short-term memory (isi run ke andar context)
        aur long-term memory (purane runs se, local ChromaDB mein save hoti
        hai `./crew_memory/` folder mein) deta hai. Agar memory setup fail
        ho (jaise embedding config ka masla), hum gracefully memory=False
        pe fallback karte hain taake pipeline crash na ho.
        """
        try:
            return Crew(
                agents=self.agents,
                tasks=self.tasks,
                process=Process.sequential,
                verbose=True,
                memory=True,
                embedder={
                    "provider": "google",
                    "config": {
                        "api_key": os.getenv("GEMINI_API_KEY"),
                        "model": "models/text-embedding-004",
                    },
                },
            )
        except Exception as e:
            print(f"[Memory setup failed, continuing WITHOUT memory: {e}]")
            return Crew(
                agents=self.agents,
                tasks=self.tasks,
                process=Process.sequential,
                verbose=True,
                memory=False,
            )
