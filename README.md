# AI Resume Analyzer & Action Plan Generator

## Why I Built This
During my research, I noticed that standard ATS (Applicant Tracking System) software rejects a massive percentage of resumes just because of formatting issues like hidden tables or multi-column layouts. I built this tool to simulate a strict ATS parser so candidates can see exactly how a machine reads their resume before they apply. It also uses AI to find skill gaps and recommend a 90-day upskilling roadmap.

## Core Features
* **ATS Layout Parsing:** Strips away visual elements and uses custom Python logic to check for unreadable formatting and multi-column breaks.
* **Domain Relevance Check:** Evaluates the candidate's past experience against the specific target role, penalizing generic resumes.
* **Recruiter Action Plan:** Generates a personalized 90-day learning roadmap and tough, role-specific interview questions.

## Technologies Used
* **Language:** Python 3
* **UI Framework:** Streamlit
* **Document Extraction:** PyPDF2 & python-docx
* **AI Backend:** Groq API (LLaMA 3 model for fast inference)

## How to Run Locally

**1. Clone the repository**
Open your terminal and run:
```bash
git clone [https://github.com/av2203/ai-resume-analyzer.git](https://github.com/av2203/ai-resume-analyzer.git)
cd ai-resume-analyzer
```

**2. Create a virtual environment (Recommended)**
This keeps the project dependencies isolated.
```bash
python -m venv venv
```
*On Mac/Linux:*
```bash
source venv/bin/activate
```
*On Windows:*
```bash
venv\Scripts\activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set up your Groq API Key**
This project requires a free Groq API key to run the AI model.
* Go to the [Groq Cloud Console](https://console.groq.com/keys) and create a free account.
* Generate a new API key.
* In your project folder, create a new folder named `.streamlit`.
* Inside that folder, create a file named `secrets.toml`.
* Add your key to the file exactly like this:
```toml
GROQ_API_KEY = "your_actual_api_key_here"
```

**5. Start the application**
```bash
streamlit run app.py
```
