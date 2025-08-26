from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yaml
from app.agent_core import plan_actions, apply_actions

with open("/opt/genai-agent/config.yaml") as f:
    CFG = yaml.safe_load(f)

app = FastAPI(title="GenAI Linux Agent")

class PlanRequest(BaseModel):
    user: str
    role: str = "operator"
    message: str

class ApplyRequest(BaseModel):
    user: str

@app.post("/plan")
def plan(req: PlanRequest):
    try:
        plan, explanation, requires_approval = plan_actions(req.user, req.role, req.message)
        return {"plan": plan, "explanation": explanation, "requires_approval": requires_approval}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/apply")
def apply(req: ApplyRequest):
    if not CFG["agent"].get("auto_apply", False):
        raise HTTPException(status_code=403, detail="Auto-apply disabled")
    return apply_actions(req.user)

@app.post("/apply_pending")
def apply_pending(req: ApplyRequest):
    return apply_actions(req.user)

@app.get("/healthz")
def healthz():
    return {"ok": True}
