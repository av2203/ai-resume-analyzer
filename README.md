# AI Resume Analyzer & Action Plan Generator

A resume analysis tool built with Python and Streamlit to help candidates evaluate their resumes for ATS compatibility, assess their relevance to a target career path, and identify areas for improvement.

The application combines custom Python-based checks with LLM-generated analysis to provide practical feedback before applying for a role.

## Why I Built This

ATS systems can make it difficult to understand why a resume may not perform well during screening. Formatting, document structure, and the relevance of a resume to a specific role can all affect how it is interpreted.

I built this project to provide a simple way to review these aspects before submitting an application. It analyzes resume structure, evaluates its relevance to a selected career path, identifies potential skill gaps, and generates recommendations for improvement.

## Core Features

### ATS Layout Analysis

- Supports resume uploads in **PDF and DOCX** formats.
- Parses resume content and checks its structure for ATS compatibility.
- Uses custom Python logic to identify potential formatting and layout issues.
- Evaluates resumes across **4 scoring dimensions**.
- Performs **4 structural compatibility checks**.

### Career & Domain Relevance

- Supports **53 career paths** across **9 professional domains**.
- Evaluates a resume against the selected target career path.
- Identifies potential gaps between the candidate's current skills and the target role.
- Helps identify areas where a resume can be made more role-specific.

### Resume Analysis

The application generates structured feedback including:

- ATS evaluation
- Resume summary
- Skill-gap analysis
- Career recommendations
- Role-specific interview questions
- Learning recommendations

### 90-Day Action Plan

Based on the selected career path and identified skill gaps, the application generates a **90-day roadmap** with recommended areas to focus on.

## How It Works

```text
Resume (PDF / DOCX)
        │
        ▼
Resume Parsing
        │
        ▼
ATS & Structure Analysis
        │
        ▼
Career Path Analysis
        │
        ▼
LLM-based Analysis
        │
        ▼
Structured Results
        │
        ├── ATS Evaluation
        ├── Resume Summary
        ├── Skill Gaps
        ├── Career Recommendations
        ├── Interview Questions
        └── 90-Day Action Plan
```


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
