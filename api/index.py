from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import os
import json
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- API KEY ----
API_KEY = os.getenv("GOOGLE_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)
    MODEL = genai.GenerativeModel("gemini-2.5-flash-lite")
else:
    MODEL = None

# ---- REQUEST MODEL ----
class AnalyzeRequest(BaseModel):
    type: str
    content: str

# ---- HELPERS ----
def extract_json(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON found")
    return json.loads(match.group())

# ---- HEALTH CHECK ----
@app.get("/health")
def health():
    return {
        "status": "ok",
        "api_key_loaded": bool(API_KEY)
    }

# ---- ANALYSIS ENDPOINT ----
@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    if not MODEL:
        return {
            "verdict": "RISKY",
            "confidence": 0.0,
            "reasons": ["API key not configured"],
            "recommendation": "Backend configuration incomplete"
        }

    prompt = f"""
You are a cybersecurity decision engine.

RULES:
- Output ONLY valid JSON
- No markdown
- No explanation text
- No code blocks

FORMAT:
{{
  "verdict": "SAFE | RISKY | DANGEROUS",
  "confidence": 0.0,
  "reasons": ["short reason"],
  "recommendation": "short action"
}}

CONTENT TYPE: {req.type}
CONTENT:
\"\"\"{req.content}\"\"\"
"""

    response = MODEL.generate_content(prompt)
    raw_text = response.text.strip()

    try:
        return extract_json(raw_text)
    except Exception:
        return {
            "verdict": "RISKY",
            "confidence": 0.5,
            "reasons": ["AI output parsing error"],
            "recommendation": "Proceed with caution"
        }
