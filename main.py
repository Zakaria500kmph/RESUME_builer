import os
import requests
import streamlit as st
from dotenv import load_dotenv
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import inch

# Load environment variables
load_dotenv()
API_KEY = os.getenv("G-Api")

# Gemini API endpoint
GEN_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

# Function to query Gemini API
def generate_resume(summary_text):
    headers = {"Content-Type": "application/json"}
    params = {"key": API_KEY}

    prompt = f"""
You are a resume expert. Given the following professional summary, extract the candidate's name if possible and generate a complete, well-formatted professional resume in plain text format.
Use clear headings (e.g., NAME, SUMMARY, SKILLS, EXPERIENCE, EDUCATION, PROJECTS), make the headings uppercase and bold, and use clean bullet points. Ensure it's ATS-optimized.
Summary: {summary_text}
    """

    data = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(GEN_URL, headers=headers, params=params, json=data)

    if response.status_code == 200:
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    else:
        return f"Error {response.status_code}: {response.text}"

# Calculate simple ATS score based on keyword matching
def calculate_ats_score(resume_text):
    keywords = ["python", "machine learning", "deep learning", "data", "ai", "project", "experience", "education"]
    score = sum(kw.lower() in resume_text.lower() for kw in keywords)
    return int((score / len(keywords)) * 100)

# Save resume to a properly formatted PDF using Platypus
def save_pdf(text, filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch
    )

    styles = getSampleStyleSheet()
    normal_style = ParagraphStyle(name='Normal', fontName='Helvetica', fontSize=11, leading=14, alignment=TA_LEFT)
    heading_style = ParagraphStyle(name='Heading', fontName='Helvetica-Bold', fontSize=14, textColor='darkblue', spaceBefore=12, spaceAfter=6)
    bullet_style = ParagraphStyle(name='Bullet', fontName='Helvetica', fontSize=11, leading=14, leftIndent=15, bulletIndent=5)

    flowables = []
    lines = text.split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            flowables.append(Spacer(1, 6))
            continue

        if line.isupper() or line.endswith(':'):
            flowables.append(Paragraph(line, heading_style))
        elif line.startswith("•") or line.startswith("-"):
            clean_line = line.replace("•■", "•").replace("■", "").strip()
            flowables.append(Paragraph(clean_line, bullet_style))
        else:
            flowables.append(Paragraph(line, normal_style))

    doc.build(flowables)

# Streamlit UI
st.set_page_config(page_title="Gemini Resume Builder", page_icon="📝")
st.title(" Gemini Resume Builder with ATS Scoring")
st.markdown("Enter your professional summary below. The AI will generate a clean, ATS-friendly resume.")

# Text input area
summary = st.text_area("Professional Summary", height=250)

# Resume generation button
if st.button("Generate Resume"):
    if not summary.strip():
        st.warning(" Please enter a professional summary.")
    else:
        with st.spinner("Generating resume using Gemini..."):
            resume_text = generate_resume(summary)

            if resume_text.startswith("Error"):
                st.error(resume_text)
            else:
                ats_score = calculate_ats_score(resume_text)
                pdf_file = "generated_resume.pdf"
                save_pdf(resume_text, pdf_file)

                st.success(" Resume successfully generated!")
                st.subheader("📄 Resume Preview:")
                st.text(resume_text)

                st.subheader(f"📊 ATS Score: {ats_score}/100")
                with open(pdf_file, "rb") as f:
                    st.download_button("⬇ Download Resume as PDF", f, file_name="Resume.pdf", mime="application/pdf")
