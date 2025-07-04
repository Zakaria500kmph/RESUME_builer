import os
import requests
import streamlit as st
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Load environment variables
load_dotenv()
API_KEY = os.getenv("G-Api")

# Gemini API URL
GEN_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

# Function to query Gemini
def generate_resume(summary_text):
    headers = {"Content-Type": "application/json"}
    params = {"key": API_KEY}

    prompt = f"""
You are a resume expert. Given the following professional summary, extract the candidate's name if possible and generate a complete, well-formatted professional resume in plain text format.
Use clear headings (e.g., Name, Summary, Skills, Experience, Education), make the headings bold and uppercase, and keep the content in clean bullet points where relevant. Ensure it's ATS-optimized.
Summary: {summary_text}
    """

    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    response = requests.post(GEN_URL, headers=headers, params=params, json=data)
    if response.status_code == 200:
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    else:
        return f"Error {response.status_code}: {response.text}"

# Simple ATS score based on keyword presence
def calculate_ats_score(resume_text):
    keywords = ["python", "machine learning", "deep learning", "data", "ai", "project", "experience", "education"]
    score = sum(kw.lower() in resume_text.lower() for kw in keywords)
    return int((score / len(keywords)) * 100)

# Save resume as PDF with basic formatting
def save_pdf(text, filename):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    y = height - 40

    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            y -= 10
            continue

        # Heuristic: bold section headings
        if line.isupper() or line.endswith(':'):
            c.setFont("Helvetica-Bold", 14)
        else:
            c.setFont("Helvetica", 10)

        c.drawString(40, y, line)
        y -= 15
        if y < 40:
            c.showPage()
            y = height - 40
    c.save()

# Streamlit App
st.set_page_config(page_title="Gemini Resume Builder", page_icon="📝")
st.title("📝 Gemini Resume Builder with ATS Scoring")
st.markdown("Enter your professional summary. The AI will extract your name and generate a complete, ATS-friendly resume.")

summary = st.text_area("Professional Summary", height=250)

if st.button("Generate Resume"):
    if not summary.strip():
        st.warning("Please enter a professional summary.")
    else:
        with st.spinner("Generating your resume..."):
            resume_text = generate_resume(summary)
            ats_score = calculate_ats_score(resume_text)
            pdf_file = "generated_resume.pdf"
            save_pdf(resume_text, pdf_file)

        st.success("Resume Generated!")

        st.subheader(" Resume Output:")
        st.text(resume_text)

        st.subheader(f" ATS Score: {ats_score}/100")

        with open(pdf_file, "rb") as f:
            st.download_button("⬇ Download PDF", f, file_name="Resume.pdf", mime="application/pdf")
