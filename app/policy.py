import yaml

def load_policy():
    with open("/opt/genai-agent/policy.yaml") as f:
        return yaml.safe_load(f)

POL = load_policy()

def matches_blocked(cmd: str) -> bool:
    """Check if command matches blocked patterns"""
    for pat in POL.get("safety", {}).get("blocked_patterns", []):
        if pat in cmd:
            return True
    if len(cmd) > POL.get("safety", {}).get("max_cmd_length", 1000):
        return True
    return False

def role_requires_approval(role: str) -> bool:
    """Check if role requires approval (always True for safety)"""
    return True

def validate_step_against_policy(step: dict) -> None:
    """Validate RunCommand steps against basic safety"""
    if step.get("tool") == "RunCommand":
        cmd = step.get("args", {}).get("cmd", "")
        if matches_blocked(cmd):
            raise PermissionError("Blocked command pattern")
        return
    raise PermissionError("Only RunCommand tool is supported")
