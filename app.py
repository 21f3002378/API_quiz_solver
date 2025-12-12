from dotenv import load_dotenv
load_dotenv()

import asyncio
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from engine.orchestrator import run_quiz_flow

EXPECTED_SECRET = os.getenv("EXPECTED_SECRET", "lolipop")

app = FastAPI()

class QuizPayload(BaseModel):
    email: str
    secret: str
    url: str

@app.post("/quiz")
async def quiz_endpoint(payload: QuizPayload):
    print("1 Received /quiz request")

    # ---- SECRET CHECK ----
    if payload.secret != EXPECTED_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")

    print("2 Valid request")

    # ---- QUIZ SOLVER ----
    task = asyncio.create_task(run_quiz_flow(payload.dict()))
    done, pending = await asyncio.wait({task}, timeout=185)

    if task not in done:
        raise HTTPException(status_code=500, detail="Timed out")

    result = task.result()

    return {"status": "done", "result": result}
