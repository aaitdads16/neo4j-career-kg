"""
Use Claude to extract required skills from a job title + company name.
Returns a list of skill strings (e.g. ["PyTorch", "NLP", "Python"]).
"""
import os
import json
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

_CACHE: dict = {}   # in-memory cache to avoid re-calling for same title

def extract_skills(title: str, company: str) -> list[str]:
    """Returns list of technical skills inferred from job title + company."""
    key = f"{title}|{company}"
    if key in _CACHE:
        return _CACHE[key]
    
    prompt = (
        f"Job: '{title}' at '{company}'\n\n"
        "List the 4-6 most likely technical skills required for this role. "
        "Focus on: programming languages, ML frameworks, domains (NLP, CV, etc.), tools.\n"
        "Return JSON only: {\"skills\": [\"skill1\", \"skill2\", ...]}"
    )
    try:
        msg = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}],
        )
        data = json.loads(msg.content[0].text.strip())
        skills = data.get("skills", [])[:6]
        _CACHE[key] = skills
        return skills
    except Exception:
        # Fallback: extract from title keywords
        fallback = []
        for kw in ["Python", "PyTorch", "NLP", "CV", "LLM", "ML", "SQL", "TensorFlow"]:
            if kw.lower() in title.lower():
                fallback.append(kw)
        _CACHE[key] = fallback
        return fallback