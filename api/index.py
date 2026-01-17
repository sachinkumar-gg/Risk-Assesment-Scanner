from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import google.generativeai as genai
import os, json, re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Serve static assets only (css, png)
app.mount("/static", StaticFiles(directory=BASE_DIR), name="static")

# ---- API KEY ----
API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL = None

if API_KEY:
    genai.configure(api_key=API_KEY)
    MODEL = genai.GenerativeModel("gemini-2.5-flash-lite")

class AnalyzeRequest(BaseModel):
    type: str
    content: str

def extract_json(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return json.loads(match.group())

# ✅ FRONTEND ENTRY (SAFE)
@app.get("/")
def serve_index():
    return FileResponse(BASE_DIR / "index.html")

# ✅ BACKEND HEALTH
@app.get("/health")
def health():
    return {"status": "ok"}

# ✅ ANALYSIS
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
    return extract_json(response.text)
