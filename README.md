# ⚡ AI Resume Analyzer & Action Plan Generator

**Capstone Project by Adityavikram Maheshwari**

A standalone web application that acts as a strict Applicant Tracking System (ATS) parser and Senior Technical Recruiter. Built using Python, Streamlit, and the Groq AI API.

## 🚀 Features
* **ATS Diagnostics:** Strips away visual formatting to evaluate resumes exactly how enterprise software does, checking for multi-column breaks and unreadable fonts.
* **Domain Match Knockout:** Mathematically penalizes resumes if the candidate's experience completely misaligns with the target role.
* **Action Plan Generation:** Generates a personalized 90-day learning roadmap, highlights critical skill gaps, and provides tough, role-specific interview questions.

## 💻 Tech Stack
* **Python 3**
* **Streamlit** (Frontend UI)
* **PyPDF2 & python-docx** (Document Parsing)
* **Groq API / LLaMA 3** (LLM Backend)

## 🛠️ How to Run Locally
1. Clone this repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Add your Groq API key to `.streamlit/secrets.toml`.
4. Run the app: `streamlit run app.py`
