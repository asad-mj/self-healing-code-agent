from fastapi import FastAPI
from pydantic import BaseModel, Field
from src.healer import SelfHealingCodeAgent, HealingReport

app = FastAPI(
    title="Autonomous Self-Healing Code Agent",
    description="Sandboxed code execution, AST security verification, and iterative traceback-driven code repair service.",
    version="1.0.0"
)

agent = SelfHealingCodeAgent(max_attempts=4)

class HealRequest(BaseModel):
    buggy_code: str = Field(..., min_length=5, description="Python function containing bugs")
    test_assertions: str = Field(..., min_length=5, description="Unit test `assert` statements")

@app.get("/health", tags=["System"])
def health_check():
    return {"status": "healthy", "service": "self-healing-code-agent", "version": "1.0.0"}

@app.post("/heal", response_model=HealingReport, tags=["Autonomous Repair"])
def run_self_healing_loop(payload: HealRequest):
    return agent.heal(
        initial_code=payload.buggy_code,
        test_assertions=payload.test_assertions
    )
