import io
import pdfplumber
import os
import google.generativeai as genai
import streamlit as st

# Configure the API key from Streamlit secrets
genai.configure(st.secrets["GOOGLE_API_KEY"])

model = genai.GenerativeModel("gemini-2.0-flash")

def read_report(file) -> str:
    """Return plain text from an uploaded PDF or text file."""
    name = file.name.lower()
    if name.endswith(".pdf"):
        text_chunks = []
        with pdfplumber.open(io.BytesIO(file.read())) as pdf:
            for page in pdf.pages:
                text_chunks.append(page.extract_text() or "")
        return "\n\n".join(text_chunks)
    else:
        # Assume text-like files
        return file.read().decode("utf-8", errors="ignore")

def chunk(s: str, max_len: int = 15000):
    """Yield safe chunks so the prompt isn't too large."""
    s = s or ""
    for i in range(0, len(s), max_len):
        yield s[i:i+max_len]

def build_prompt(user_note: str, ticker: str) -> str:
    """Build the prompt for the equity research analysis."""
    return f"""
As an equity research analyst, analyze the provided report excerpt(s) and deliver a concise, professional analysis in Markdown format. Present the analysis as a direct, objective report without referencing the process of reviewing excerpts or using a model. Focus on actionable insights, explicitly noting any missing information without speculation. Structure the response as follows:

# Executive Summary
- Provide 3–6 bullets summarizing key findings, focusing on financial performance, strategic developments, and market positioning.

# Key Highlights
- Highlight primary drivers of performance, potential catalysts for growth, and notable operational or strategic achievements.

# Concerns and Risks
- Identify red flags, including issues in accounting practices, liquidity constraints, guidance reliability, or customer/supplier concentration risks.

# Quality of Earnings and Cash Flow
- Analyze working capital trends, free cash flow conversion, and sustainability of earnings.

Context:
- Ticker: {ticker or 'N/A'}
- User Note: {user_note or 'N/A'}
"""

def analyze_report(file, ticker: str, user_note: str) -> str:
    """Analyze the uploaded report and return the generated review."""
    try:
        raw_text = read_report(file)
        if not raw_text.strip():
            return "Couldn’t extract any text from the file."

        prompt = build_prompt(user_note, ticker)
        contents = [{"role": "user", "parts": prompt}]
        for i, c in enumerate(chunk(raw_text)):
            contents.append({"role": "user", "parts": f"[REPORT CHUNK {i+1}]\n{c}"})

        resp = model.generate_content(contents=contents)
        return resp.text or "_No response text returned._"

    except Exception as e:
        return f"Error analyzing the report: {e}"