"""
R&D Agent Copilot — FastAPI 应用入口。

启动方式：
    uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.mock import router as mock_router
from app.api.runs import router as runs_router

app = FastAPI(
    title="R&D Agent Copilot",
    version="0.1.0",
    description="AI 研发排障智能助手 — Day1 Agent Pipeline",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(runs_router)
app.include_router(mock_router)


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}
