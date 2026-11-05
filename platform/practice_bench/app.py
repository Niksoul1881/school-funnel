"""Local practice bench API and static frontend."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import engine

ROOT = Path(__file__).resolve().parent
app = FastAPI(title="Платформа практики · локальный стенд")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


class CreateBot(BaseModel):
    template: str
    brief: dict = {}


class ChatIn(BaseModel):
    text: str = ""
    action: str = ""


@app.get("/")
def index():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/api/templates")
def templates():
    return {
        "templates": [
            {
                "id": key,
                "name": value["name"],
                "icon": value["icon"],
                "tagline": value["tagline"],
                "fields": value["fields"],
                "defaults": value["defaults"],
                "accent": value["accent"],
            }
            for key, value in engine.TEMPLATES.items() if key != "ai"
        ]
    }


@app.get("/api/bots")
def bots():
    return {"bots": [{"id": bot["id"], "template": bot["template"], "name": bot["name"]} for bot in engine.BOTS.values()]}


@app.get("/api/bots/{bot_id}")
def bot_detail(bot_id: str):
    bot = engine.BOTS.get(bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Бот не найден")
    return {"bot": bot}


@app.post("/api/bots")
def create(data: CreateBot):
    try:
        bot = engine.create_bot(data.template, data.brief)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"bot": {"id": bot["id"], "template": bot["template"], "name": bot["name"]}}


@app.delete("/api/bots/{bot_id}")
def delete(bot_id: str):
    engine.BOTS.pop(bot_id, None)
    engine.SESSIONS.pop(bot_id, None)
    return {"ok": True}


@app.post("/api/bots/{bot_id}/message")
def chat(bot_id: str, data: ChatIn):
    if bot_id not in engine.BOTS:
        raise HTTPException(status_code=404, detail="Бот не найден")
    try:
        replies = engine.message(bot_id, data.text, data.action)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"messages": replies}


@app.post("/api/bots/{bot_id}/reset")
def reset(bot_id: str):
    if bot_id not in engine.BOTS:
        raise HTTPException(status_code=404, detail="Бот не найден")
    engine.reset(bot_id)
    return {"messages": engine.message(bot_id, action="start")}

