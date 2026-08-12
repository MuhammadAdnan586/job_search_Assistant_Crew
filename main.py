"""
Ye entry point hai — is file ko run karke poora pipeline chalta hai.

Command: python main.py
"""

from src.job_search_crew.crew import JobSearchCrew


def run():
    # Yahan apni details daal dein — ye 'inputs' tasks.yaml ke andar
    # {job_title}, {location}, {user_background} ki jagah jayenge
    inputs = {
        "job_title": "Python Developer",
        "location": "Rawalpindi, Pakistan",
        "user_background": (
            "Computer Science graduate, Full-Stack Web Developer intern, "
            "FastAPI, Next.js, MySQL, aur ek AutoML SaaS platform banaya "
            "hai jisme SHAP explainability aur Gemini chatbot integration hai."
        ),
    }

    result = JobSearchCrew().crew().kickoff(inputs=inputs)

    print("\n\n========== FINAL RESULT ==========\n")
    print(result)


if __name__ == "__main__":
    run()
