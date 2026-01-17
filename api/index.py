from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
import os
import json
import re

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("API key not found")

genai.configure(api_key=API_KEY)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    type: str
    content: str

MODEL = genai.GenerativeModel("gemini-2.5-flash-lite")

def extract_json(text: str):
    """
    Extract JSON object from Gemini response safely
    """
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON found")
    return json.loads(match.group())

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
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
    except Exception as e:
        print("RAW GEMINI OUTPUT:", raw_text)
        return {
            "verdict": "RISKY",
            "confidence": 0.5,
            "reasons": ["AI output format error"],
            "recommendation": "Proceed with caution"
        }
