import json, time
from pathlib import Path

LOG = Path("/opt/genai-agent/logs/audit.jsonl")
LOG.parent.mkdir(parents=True, exist_ok=True)

def audit_log(**kwargs):
    with open(LOG, "a") as f:
        f.write(json.dumps({"ts": time.time(), **kwargs}) + "\n")
