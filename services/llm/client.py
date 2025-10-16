import os, requests, hashlib
import json, re

LLM_URL = os.getenv("LLM_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "mistral:7b-instruct-q4_0")  # see model picks below

def prompt_hash(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:10]

def generate_bullets(system: str, user: str, seed: int = 7, temperature: float = 0.0) -> list[str]:
    payload = {
        "model": LLM_MODEL,
        "options": {"seed": seed, "temperature": temperature},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
    }
    r = requests.post(f"{LLM_URL}/v1/chat/completions", json=payload, timeout=120)
    r.raise_for_status()
    text = r.json()["choices"][0]["message"]["content"]
    # normalize to bullets
    bullets = []
    for line in text.splitlines():
        line = line.strip(" -•\t")
        if line:
            bullets.append(line)
    return bullets[:10]

def _extract_first_json(text: str):
    """
    Robustly extract the first JSON object/array from a model reply.
    Handles accidental code fences or prose around the JSON.
    """
    # Strip common code fences
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    # Try direct parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # Fallback: find the first {...} or [...] block
    start_candidates = [m.start() for m in re.finditer(r"[\{\[]", text)]
    for start in start_candidates:
        for end in range(len(text), start, -1):
            chunk = text[start:end]
            try:
                return json.loads(chunk)
            except Exception:
                continue
    return {}


def generate_json(system: str, user: str, seed: int = 7, temperature: float = 0.0) -> dict:
    """
    Calls chat completions and returns parsed JSON as an object (dict).
    """
    payload = {
        "model": LLM_MODEL,
        "options": {"seed": seed, "temperature": temperature},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
    }
    r = requests.post(f"{LLM_URL}/v1/chat/completions", json=payload, timeout=120)
    r.raise_for_status()
    text = r.json()["choices"][0]["message"]["content"]
    parsed = _extract_first_json(text)

    # Coerce to dict: return empty object if not dict (optional)
    return parsed if isinstance(parsed, dict) else {}
