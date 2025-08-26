import json
from pathlib import Path

STATE_DIR = Path("/opt/genai-agent/logs")
STATE_DIR.mkdir(parents=True, exist_ok=True)

def pending_file(user: str):
    return STATE_DIR / f"pending_{user}.json"

def save_pending(user: str, plan):
    pending_file(user).write_text(json.dumps(plan, indent=2))

def load_pending(user: str):
    pf = pending_file(user)
    return json.loads(pf.read_text()) if pf.exists() else None

def clear_pending(user: str):
    pf = pending_file(user)
    pf.unlink() if pf.exists() else None

def history_file(user: str):
    return STATE_DIR / f"history_{user}.jsonl"

def add_history(user: str, role: str, content: str):
    with open(history_file(user), "a") as f:
        f.write(json.dumps({"role": role, "content": content}) + "\n")

def get_recent_history(user: str, max_lines: int = 10):
    hf = history_file(user)
    if not hf.exists():
        return []
    lines = hf.read_text().splitlines()[-max_lines:]
    return [json.loads(line) for line in lines if line.strip()]
