import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def call_gemini(prompt: str, temperature: float = 0.1) -> str:
    """Call Gemini and return text output"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    
    resp = model.generate_content(
        prompt,
        generation_config={"temperature": temperature, "max_output_tokens": 1024}
    )
    return resp.text if hasattr(resp, "text") else str(resp)
