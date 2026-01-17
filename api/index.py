from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import google.generativeai as genai
import os, json, re

API_KEY = os.getenv("GOOGLE_API_KEY")
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

# 🔥 Serve frontend
app.mount("/", StaticFiles(directory=".", html=True), name="static")

class AnalyzeRequest(BaseModel):
    type: str
    content: str

MODEL = genai.GenerativeModel("gemini-2.5-flash-lite")

def extract_json(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return json.loads(match.group())

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    response = MODEL.generate_content(f"""
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
""")
    return extract_json(response.text)
