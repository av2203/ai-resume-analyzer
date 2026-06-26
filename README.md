# AI RESUME ANALYZER

## Why I Built This
During my research, I noticed that standard ATS (Applicant Tracking System) software rejects a massive percentage of resumes just because of formatting issues like hidden tables or multi-column layouts. I built this tool to simulate a strict ATS parser so candidates can see exactly how a machine reads their resume before they apply. It also uses AI to find skill gaps and recommend a 90-day upskilling roadmap.

## Core Features
* **ATS Layout Parsing:** Strips away visual elements and uses custom Python regex logic to check for unreadable formatting and multi-column breaks.
* **Domain Relevance Check:** Evaluates the candidate's past experience against the specific target role, penalizing generic resumes.
* **Recruiter Action Plan:** Generates a personalized 90-day learning roadmap and tough, role-specific interview questions.

## Technologies Used
* **Language:** Python 3
* **UI Framework:** Streamlit
* **Document Extraction:** PyPDF2 & python-docx
* **AI Backend:** Groq API (LLaMA 3 model for fast inference)

## How to Run Locally
1. Clone this repository to your local machine.
2. Install the required libraries: `pip install -r requirements.txt`
3. Create a `.streamlit/secrets.toml` file and add your Groq API key: `GROQ_API_KEY = "your_key_here"`
4. Start the server: `streamlit run app.py`
