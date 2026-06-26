import streamlit as st
from PyPDF2 import PdfReader
import docx
import re
from groq import Groq
import json
import time

# Page config & CSS
st.set_page_config(page_title="AI Resume Analyzer", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    /* HIDE STREAMLIT DEFAULT UI (Deploy Button, Menu, Footer) */
    .stAppDeployButton { display: none !important; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    .main { padding-top: 1.5rem; }
    [data-testid="column"] { padding: 0 1rem; }
    h1, h2, h3 { text-align: center; margin-bottom: 1.5rem; }
    
    /* Beautiful Metric Cards */
    div[data-testid="metric-container"] {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #f39c12;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* PREMIUM TAB STYLING */
    .stTabs [data-baseweb="tab-list"] { 
        gap: 8px; 
        width: 100%; 
        background-color: transparent; 
    }
    .stTabs [data-baseweb="tab"] { 
        flex: 1; 
        justify-content: center;
        height: 60px; 
        font-size: 1.15rem; 
        background-color: #f1f3f6; 
        border-radius: 8px 8px 0px 0px; 
        border: 1px solid #e0e0e0;
        border-bottom: none;
        transition: all 0.3s ease;
    }
    .stTabs [aria-selected="true"] { 
        background-color: #ffffff; 
        border-top: 4px solid #f39c12; 
        font-weight: 800;
        color: #333333;
        box-shadow: 0px -4px 10px rgba(0,0,0,0.02); 
    }
    .stAlert { border-radius: 8px; }
    
    /* ATS Checklist Styling */
    .ats-check-row { display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #eee; font-size: 1.05rem; }
    .ats-pass { color: #2ecc71; font-weight: bold; }
    .ats-fail { color: #e74c3c; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# API key
try:
    api_key = st.secrets["GROQ_API_KEY"]
except Exception:
    st.error("🚨 API Key missing. Please add GROQ_API_KEY to your .streamlit/secrets.toml file.")
    st.stop()

# Model cascade (Groq specific)
MODEL_CASCADE = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768"
]

# Job roles (grouped by domain for the dropdown)
JOB_ROLES = [
    # Technology & Engineering
    "Frontend Developer",
    "Backend Developer",
    "Full Stack Developer",
    "Python Developer",
    "Java Developer",
    "DevOps Engineer",
    "Cloud Engineer",
    "Cybersecurity Analyst",
    "Mobile App Developer",
    "Embedded Systems Engineer",
    "QA / Test Engineer",
    "Blockchain Developer",

    # Data & AI
    "Data Scientist",
    "Data Analyst",
    "Data Engineer",
    "Machine Learning Engineer",
    "AI Research Scientist",
    "Business Intelligence Analyst",

    # Business & Management
    "Business Analyst",
    "Project Manager",
    "Product Manager",
    "Operations Manager",
    "Supply Chain Manager",
    "Management Consultant",
    "Strategy Analyst",

    # Finance & Accounting
    "Financial Analyst",
    "Investment Banking Analyst",
    "Chartered Accountant",
    "Risk Analyst",
    "Equity Research Analyst",
    "Audit Associate",

    # Marketing & Sales
    "Digital Marketing Specialist",
    "Content Strategist",
    "SEO Specialist",
    "Brand Manager",
    "Sales Executive",
    "Growth Hacker",

    # Human Resources
    "HR Manager",
    "HR Business Partner",
    "Talent Acquisition Specialist",
    "Learning & Development Manager",

    # Design & Creative
    "UI/UX Designer",
    "Graphic Designer",
    "Product Designer",
    "Motion Designer",

    # Legal & Compliance
    "Corporate Lawyer",
    "Compliance Officer",
    "Legal Analyst",

    # Healthcare & Life Sciences
    "Clinical Data Analyst",
    "Healthcare Administrator",
    "Medical Affairs Specialist",
    "Pharmacovigilance Analyst",

    # Custom
    "✏️  Other (Type Your Own)",
]

# Session state
for key, default in [
    ("ai_response", None), ("ats_score", 0),
    ("matched_skills", []), ("missing_skills", []),
    ("previous_role", "Frontend Developer"),
    ("ai_breakdown", None), ("resume_text", ""),
    ("model_used", None),
    ("custom_role_text", ""),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# Helpers
def sanitize_resume_text(text):
    text = re.sub(r'\n{3,}', '\n\n', text)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return "\n".join(lines)

def extract_text_from_pdf(file):
    """
    Extracts text while PRESERVING line structure.
    - Uses standard extract_text() (not layout mode) so lines stay clean.
    - Only fixes hyphenated line-breaks and excessive blank lines.
    - Keeps newlines so the AI sees the resume as structured text,
      NOT as one collapsed blob (which caused false column detection).
    """
    reader = PdfReader(file)
    pages = []
    for page in reader.pages:
        raw = page.extract_text() or ""
        pages.append(raw)

    text = "\n".join(pages)
    text = re.sub(r'-\n', '', text)
    lines = []
    for line in text.split('\n'):
        line = re.sub(r' {3,}', '  ', line)
        lines.append(line)
    text = re.sub(r'\n{3,}', '\n', '\n'.join(lines))
    return text.strip()

def extract_text_from_docx(file):
    doc = docx.Document(file)
    text = "\n".join(p.text for p in doc.paragraphs)
    return sanitize_resume_text(text)

def detect_column_layout(text):
    """
    Code-based column detector replaces AI guesswork with deterministic logic.
    """
    lines = [l for l in text.split('\n') if len(l.strip()) > 15]
    if not lines:
        return False

    column_lines = 0
    for line in lines:
        segments = re.split(r' {3,}', line.strip())
        non_empty = [s.strip() for s in segments if s.strip()]
        if len(non_empty) >= 2 and all(len(s) > 25 for s in non_empty):
            column_lines += 1

    ratio = column_lines / max(len(lines), 1)
    return ratio > 0.20

# Core AI call (Groq)
def call_groq(prompt, client, label="", is_json=False):
    for model in MODEL_CASCADE:
        for attempt in range(2):
            try:
                kwargs = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.05,
                    "max_tokens": 2000
                }
                if is_json:
                    kwargs["response_format"] = {"type": "json_object"}

                response = client.chat.completions.create(**kwargs)
                return response.choices[0].message.content, model

            except Exception as e:
                err = str(e).lower()
                if "429" in err or "rate limit" in err or "503" in err:
                    if attempt == 0:
                        time.sleep(3)
                        continue
                    else:
                        break 
                break

    return None, None

# ATS analysis
def analyse_resume(resume_text, target_role, client):
    prompt = f"""
You are a RUTHLESS, strictly logical ATS (Applicant Tracking System) parser and Senior Technical Recruiter hiring for a {target_role} position.

Read the text parsed from the candidate's resume below. 

RESUME:
{resume_text[:5000]}

CRITICAL SCORING RULES - READ CAREFULLY:
1. DOMAIN MATCH KNOCKOUT: Evaluate RELEVANCE, not just quality. If the candidate applies for '{target_role}' but has experience only in a completely different field, penalize overall_score below 30.
2. EXPERIENCE IMPACT: Score strictly on how relevant past experience is to '{target_role}'. Prestigious but irrelevant jobs = 0-20%.
3. ATS FORMATTING EVALUATION - STRICT RULES:
   - The field "no_complex_columns_detected" has already been evaluated by code. You MUST use the pre-computed value: {{column_safe}}.
   - DO NOT override this based on the text appearance. The code is authoritative.
   - A TRUE multi-column layout means two content streams running side-by-side like a Word two-column document.
   - Right-aligned dates on the same line as job titles (e.g. "Company Name    2020-2022") is NORMAL and ACCEPTABLE - NOT a column issue.
   - Section-level bullet lists that happen to be arranged in columns (like a skills list) are acceptable.

Return ONLY a valid JSON object matching this exact structure:
{{
  "overall_score": 85,
  "category_scores": {{
    "ats_parse_rate": 80,
    "skills_match": 90,
    "experience_impact": 85,
    "education_alignment": 90
  }},
  "ats_diagnostics": {{
    "has_standard_sections": true,
    "contact_info_readable": true,
    "no_complex_columns_detected": false,
    "dates_chronological": true
  }},
  "matched_skills": ["Python", "SQL", "AWS"],
  "missing_skills": ["Docker", "Kubernetes"],
  "strengths": ["Strong backend experience", "Quantifiable bullet points"],
  "weaknesses": ["Lacks containerization", "Passive language used"],
  "ats_structural_feedback": ["The parsed text appears disjointed, indicating a multi-column layout was used which will break ATS.", "Missing a dedicated 'Work Experience' or 'Projects' section header."],
  "quick_tips": ["Change to a single-column layout (e.g., Harvard format)", "Use standard section names"]
}}
"""
    column_detected = detect_column_layout(resume_text)
    column_safe = "false (no complex columns detected - mark no_complex_columns_detected as true)" if column_detected else "true (single-column layout confirmed - mark no_complex_columns_detected as true)"
    prompt = prompt.replace("{column_safe}", column_safe)

    raw, model = call_groq(prompt, client, label="ATS analysis", is_json=True)

    if raw is None:
        return None, None

    start_idx = raw.find('{')
    end_idx = raw.rfind('}')
    
    if start_idx != -1 and end_idx != -1:
        raw = raw[start_idx:end_idx+1]

    try:
        return json.loads(raw), model
    except json.JSONDecodeError:
        return None, None

# Action Plan Generator
def generate_coaching(resume_text, target_role, breakdown, client):
    matched   = ", ".join(breakdown.get("matched_skills", []))
    missing   = ", ".join(breakdown.get("missing_skills", []))
    strengths = ", ".join(breakdown.get("strengths", []))
    gaps      = ", ".join(breakdown.get("weaknesses", []))
    structural = ", ".join(breakdown.get("ats_structural_feedback", []))
    score     = breakdown.get("overall_score", 0)

    prompt = f"""
You are an elite Technical Recruiter and Career Strategist. The user is a candidate applying for a {target_role} position. 

Candidate Data:
- Target Role: {target_role}
- ATS Match Score: {score}/100
- Present Skills: {matched}
- Missing Skills: {missing}
- Structural/ATS Issues: {structural}
- Weaknesses/Gaps: {gaps}

TASK: Write a highly actionable, direct, and specific Action Plan FOR THE CANDIDATE. 
RULES:
1. Speak DIRECTLY to the candidate using "You" and "Your". DO NOT use third-person pronouns ("The candidate").
2. Be brutally honest but highly constructive. No generic fluff.
3. Use rich markdown (bolding, bullet points) to make it scannable. Give highly specific advice (e.g., name actual types of projects to build, or specific formatting rules).

Structure the response EXACTLY with these headings:

## 1. The Reality Check (ATS & Domain Match)
Critique their current layout and domain relevance. Tell them exactly why they got a {score}/100. Be strict. Tell them exactly how to fix their formatting (e.g., single-column Harvard format) and if they need a serious career pivot.

## 2. Your Critical Skill Gaps
List the absolute mandatory skills they are missing for a {target_role}. Explain *why* these matter in the real world.

## 3. Your 90-Day Execution Roadmap
Break down exactly what they need to do over the next 3 months to become hirable for this role. Be hyper-specific.
* **Month 1 (Upskilling):** Suggest specific technical concepts they must master.
* **Month 2 (Portfolio Building):** Suggest 1-2 SPECIFIC, impressive portfolio projects they should build related to {target_role}.
* **Month 3 (Refinement):** Suggest how they should update their resume and network.

## 4. Hard Interview Questions You Will Face
Provide 5 tough, role-specific questions (technical or behavioral) based on their specific background and gaps. DO NOT ask generic questions like "What are your strengths?"

## 5. Do This Today (Next 24 Hours)
Give 3 highly specific, immediate tasks they can execute right now to fix their resume.
"""
    text, model = call_groq(prompt, client, label="action plan", is_json=False)
    return text, model

# UI Application

# Premium Hero Section
st.markdown("""
    <div style='text-align: center; margin-top: -2rem; margin-bottom: 2rem;'>
        <h1 style='font-size: 3.5rem; margin-bottom: 0.5rem;'>⚡ AI Resume Analyzer</h1>
        <p style='font-size: 1.2rem; color: #666;'>Bypass the ATS black hole. Get a ruthless layout diagnostic and a strict 90-day recruiter action plan.</p>
    </div>
""", unsafe_allow_html=True)

# Feature Cards to fill the empty space
step1, step2, step3 = st.columns(3)
with step1:
    st.info("**🎯 1. Select Target Role**\n\nTell the AI exactly what job you want so it can ruthlessly evaluate your domain match.")
with step2:
    st.info("**📄 2. Upload Resume**\n\nDrop your PDF or DOCX. We strip away the visuals to see exactly what an ATS bot sees.")
with step3:
    st.info("**🚀 3. Get Action Plan**\n\nReceive a strict formatting score, critical skill gap analysis, and a personalized 90-day roadmap.")

st.divider()
st.markdown("### Let's Get Started")

col_role, _ = st.columns([2, 1])
with col_role:
    selected_option = st.selectbox("🎯 Target Job Role", JOB_ROLES)

# Custom role input
if selected_option == "✏️  Other (Type Your Own)":
    st.write("")
    custom_input = st.text_input(
        "✍️ Enter your target job role:",
        placeholder="e.g. Actuary, Urban Planner, Sports Analyst, Radiologist, Architect...",
        value=st.session_state.custom_role_text,
        help="Type any job role — the AI will analyse the resume specifically for that position."
    )
    st.session_state.custom_role_text = custom_input.strip()
    target_role = st.session_state.custom_role_text

    if not target_role:
        st.info("👆 Type your target job role above and then upload your resume.")
        st.stop()
    else:
        st.caption(f"Analysing for: **{target_role}**")
else:
    target_role = selected_option
    st.session_state.custom_role_text = ""

# Reset analysis state whenever the effective role changes
if target_role != st.session_state.previous_role:
    for k in ["ai_response", "ai_breakdown", "matched_skills", "missing_skills", "model_used"]:
        st.session_state[k] = None if k in ["ai_response", "ai_breakdown", "model_used"] else []
    st.session_state.ats_score = 0
    st.session_state.previous_role = target_role

st.write("")
uploaded_file = st.file_uploader(
    "Upload your resume (PDF or DOCX)", type=["pdf", "docx"],
    label_visibility="collapsed"
)

if uploaded_file is not None:
    ext = uploaded_file.name.split(".")[-1].lower()

    with st.spinner("📄 Reading resume..."):
        if ext == "pdf":
            resume_text = extract_text_from_pdf(uploaded_file)
        else:
            resume_text = extract_text_from_docx(uploaded_file)
        st.session_state.resume_text = resume_text

    if not resume_text.strip():
        st.error("❌ Could not extract text from this file. Try a different PDF or convert to DOCX.")
        st.stop()
        
    st.success("✅ Resume parsed successfully!")

    # Run AI analysis
    with st.spinner("⚡ Analyzing your ATS layout and skills..."):
        client = Groq(api_key=api_key)
        ai_breakdown, model_used = analyse_resume(resume_text, target_role, client)

    if ai_breakdown:
        st.session_state.ai_breakdown   = ai_breakdown
        st.session_state.ats_score      = ai_breakdown.get("overall_score", 0)
        st.session_state.matched_skills = ai_breakdown.get("matched_skills", [])
        st.session_state.missing_skills = ai_breakdown.get("missing_skills", [])
        st.session_state.model_used     = model_used
    else:
        st.error("❌ **The AI models are currently unavailable or rate-limited.** Please wait 60 seconds and try again.")
        st.stop()

    st.divider()

    # Tabs
    tab1, tab2 = st.tabs(["📊 ATS & Layout Score", "🤖 Action Plan"])

    # TAB 1
    with tab1:
        st.subheader(f"ATS Compatibility — {target_role}")
        data = st.session_state.ai_breakdown
        score = data.get("overall_score", 0)

        # Score display
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if score >= 80:
                color, label = "#2ecc71", "Excellent ✅"
            elif score >= 60:
                color, label = "#f39c12", "Good 👍"
            elif score >= 30:
                color, label = "#e67e22", "Needs Work ⚠️"
            else:
                color, label = "#e74c3c", "Major Mismatch ❌"
                
            st.markdown(f"<h1 style='text-align:center;color:{color};font-size:4rem;'>{score}%</h1>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align:center;font-size:1.2rem;color:{color};'><strong>{label}</strong></p>", unsafe_allow_html=True)

        st.progress(min(score / 100.0, 1.0))
        st.write("")

        # Top Level Splits
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("### 🛠️ ATS Parser Diagnostics")
            st.info("Most resumes fail here. We test if standard hiring software can read your layout without breaking.")
            
            checks = data.get("ats_diagnostics", {})
            
            def render_check(label, passed):
                icon = "<span class='ats-pass'>✅ Passed</span>" if passed else "<span class='ats-fail'>❌ Failed</span>"
                st.markdown(f"<div class='ats-check-row'><span>{label}</span> {icon}</div>", unsafe_allow_html=True)

            render_check("Standard Sections Used", checks.get("has_standard_sections", False))
            render_check("Contact Info Readable", checks.get("contact_info_readable", False))
            render_check("Simple Layout (No Columns/Tables)", checks.get("no_complex_columns_detected", False))
            render_check("Dates in Chronological Order", checks.get("dates_chronological", False))
            
            st.write("")
            st.markdown("#### ATS Layout Feedback")
            for item in data.get("ats_structural_feedback", []):
                st.write(f"• {item}")

        with col_right:
            st.markdown("### 📈 Category Breakdown")
            cats = data.get("category_scores", {})
            st.metric("ATS Parse Rate (Formatting)", f"{cats.get('ats_parse_rate', 0)}%")
            st.metric("Skills Match", f"{cats.get('skills_match', 0)}%")
            st.metric("Experience Impact", f"{cats.get('experience_impact', 0)}%")

            st.markdown("#### 💡 Quick Improvement Tips")
            for i, tip in enumerate(data.get("quick_tips", []), 1):
                st.write(f"{i}. {tip}")

        st.write("---")
        st.markdown("### 🔍 Content & Skill Analysis")
        sk1, sk2 = st.columns(2)
        with sk1:
            st.success("✅ Skills & Strengths Found")
            for skill in data.get("matched_skills", []):
                st.markdown(f"- **{skill}**")
            for s in data.get("strengths", []):
                st.markdown(f"- *{s}*")
        with sk2:
            st.error("⚠️ Skills to Develop & Gaps")
            missing = data.get("missing_skills", [])
            if missing:
                for skill in missing:
                    st.markdown(f"- **{skill}**")
            for w in data.get("weaknesses", []):
                st.markdown(f"- *{w}*")

    # TAB 2
    with tab2:
        st.subheader("🤖 Recruiter Action Plan")

        if not st.session_state.ai_breakdown:
            st.info("Upload a resume first to generate your action plan.")
        else:
            if st.button("✨ Generate Action Plan", type="primary", use_container_width=True):
                with st.spinner("Writing your personalised action plan..."):
                    client = Groq(api_key=api_key)
                    report, model = generate_coaching(
                        st.session_state.resume_text,
                        target_role,
                        st.session_state.ai_breakdown,
                        client
                    )
                    if report:
                        st.session_state.ai_response = report
                        st.success("✅ Action Plan ready!")
                    else:
                        st.error("❌ Could not generate plan. Please wait a minute and try again.")

            if st.session_state.ai_response:
                st.markdown("---")
                st.markdown(st.session_state.ai_response)
                st.download_button(
                    label="📥 Download Action Plan",
                    data=st.session_state.ai_response,
                    file_name=f"{target_role.replace(' ', '_')}_Action_Plan.txt",
                    mime="text/plain",
                    use_container_width=True
                )