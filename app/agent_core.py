import json, re, subprocess
from typing import Tuple, List, Dict
from app.llm_gemini import call_gemini
from app import state, audit

SYSTEM_PROMPT = """You convert English requests into shell commands for this Linux host.
Output ONLY: {"commands": ["<cmd1>", "<cmd2>"], "explanation": "..."}
- Each command must be complete and runnable
- Use sudo when needed for privileged operations
- Respect the OS info provided"""

def _extract_json(text: str) -> Dict:
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.S)
        return json.loads(m.group(0)) if m else {}

def _exec_shell(command: str, timeout: int = 300) -> Dict:
    try:
        p = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
        return {"returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr}
    except Exception as e:
        return {"error": str(e)}

def _get_system_context() -> str:
    try:
        with open("/etc/os-release") as f:
            return f.read().strip()
    except Exception:
        return ""

def _commandify(user_message: str, os_info: str) -> str:
    """Generate a single command if LLM fails"""
    cmd_prompt = f"""Convert this request to ONE shell command:
OS: {os_info}
Request: {user_message}
Command:"""
    try:
        resp = call_gemini(cmd_prompt, temperature=0.0)
        return resp.strip().splitlines()[0].strip()
    except Exception:
        return "uname -a"

def plan_actions(user: str, role: str, message: str) -> Tuple[List[Dict], str, bool]:
    os_info = _get_system_context()
    recent = state.get_recent_history(user, max_lines=5)
    hist_blob = "\n".join(f"{h['role']}: {h['content']}" for h in recent)
    
    prompt = f"{SYSTEM_PROMPT}\nOS: {os_info}\nChat: {hist_blob}\nUser: {message}\nJSON:"
    raw = call_gemini(prompt, temperature=0.1)
    data = _extract_json(raw)
    
    commands = data.get("commands", [])
    if not commands:
        cmd = _commandify(message, os_info)
        commands = [cmd]
    
    plan = [{"tool": "RunCommand", "action": "run", "args": {"cmd": c}, "why": "command"} for c in commands if c.strip()]
    explanation = data.get("explanation", "Generated commands for your request")
    
    state.save_pending(user, {"plan": plan, "explanation": explanation})
    state.add_history(user, "user", message)
    state.add_history(user, "assistant", f"Executed: {len(plan)} commands")
    audit.audit_log(event="PLAN", user=user, role=role, message=message, plan=plan)
    
    return plan, explanation, True

def apply_actions(user: str) -> Dict:
    pending = state.load_pending(user)
    if not pending:
        return {"error": "no pending plan"}
    
    plan = pending.get("plan", [])
    results = []
    for step in plan:
        cmd = step.get("args", {}).get("cmd", "")
        res = _exec_shell(cmd)
        results.append({"step": step, "result": res})
    
    state.clear_pending(user)
    audit.audit_log(event="APPLY", user=user, result=results)
    return {"applied": results}
