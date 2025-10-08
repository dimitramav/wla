import os, requests, hashlib

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
