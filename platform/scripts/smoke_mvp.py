#!/usr/bin/env python3
"""Смоук-тест MVP. Запускать при работающем сервере:

    python scripts/smoke_mvp.py

Проверяет: health, вход демо, каталог, создание проекта, чат, превью,
уроки, пополнение, админку и отказ по фальшивому токену.
"""
from __future__ import annotations

import sys
import time

import httpx

BASE = "http://127.0.0.1:8000"


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print("  ok:", message)


def main() -> int:
    c = httpx.Client(base_url=BASE, timeout=30)
    print("health")
    r = c.get("/api/health")
    check(r.status_code == 200 and r.json().get("ok"), "сервер отвечает")

    print("demo login")
    r = c.post("/api/auth/login", json={"email": "demo@school.local", "password": "demo1234"})
    check(r.status_code == 200, "вход demo@school.local")
    check(r.json()["user"]["token_balance"] >= 0, "токены приходят")

    print("catalog")
    templates = c.get("/api/catalog").json()["templates"]
    check(len(templates) >= 6, f"шаблонов: {len(templates)}")
    check(any(t["id"] == "bot-vizitka" for t in templates), "есть бот-визитка")

    print("create project")
    brief = {
        "business_name": "Смоук Студия",
        "niche": "студия",
        "product": "услуги",
        "audience": "люди",
        "goal": "заявки",
        "tone": "дружелюбно",
        "price": "стрижка — 3000 ₽",
        "faq": "Вопрос?|Ответ.",
        "contact": "@smoke",
        "payment": "none",
        "accent": "#3ec7ff",
    }
    r = c.post("/api/projects", json={"template_id": "bot-vizitka", "name": "Смоук Студия", "brief": brief})
    check(r.status_code == 200, "проект создан")
    pid = r.json()["id"]
    project = c.get(f"/api/projects/{pid}").json()["project"]
    check(any(f["path"] == "content.json" for f in project["files"]), "content.json сгенерирован")

    print("agent chat")
    r = c.post(f"/api/projects/{pid}/chat", json={"message": "добавь меню: Услуги, Записаться, Цены, Связаться"})
    check(r.status_code == 200, "агент ответил")
    check("Обновил меню" in r.json()["message"], "меню обновлено")
    content = next(f["content"] for f in r.json()["project"]["files"] if f["path"] == "content.json")
    check("Услуги" in content, "тексты в content.json")

    print("lessons")
    lessons = c.get("/api/lessons").json()["lessons"]
    check(len(lessons) == 6, "6 уроков")
    r = c.post("/api/lessons/l3/complete")
    check(r.status_code == 200, "урок отмечается")

    print("billing")
    before = c.get("/api/me").json()["user"]["token_balance"]
    r = c.post("/api/billing/topup", json={"package_id": "start"})
    check(r.status_code == 200 and r.json()["balance"] > before, "демо-пополнение токенов")

    print("miniapp preview")
    r = c.post(
        "/api/projects",
        json={
            "template_id": "miniapp-showcase",
            "name": "Смоук Витрина",
            "brief": {**brief, "business_name": "Смоук Витрина", "sections": "Главная, Каталог"},
        },
    )
    check(r.status_code == 200, "мини-апп создан")
    mpid = r.json()["id"]
    preview = c.get(f"/api/projects/{mpid}/preview")
    check(preview.status_code == 200 and "Смоук Витрина" in preview.text, "превью мини-аппа")

    print("deploy rejects fake token")
    r = c.post(f"/api/projects/{pid}/deploy", json={"token": "123:fake"})
    check(r.status_code == 400, "фальшивый токен отклонён")

    print("admin")
    a = httpx.Client(base_url=BASE, timeout=30)
    r = a.post("/api/auth/login", json={"email": "admin@school.local", "password": "admin1234"})
    check(r.status_code == 200, "вход админа")
    stats = a.get("/api/admin/stats")
    check(stats.status_code == 200 and stats.json()["users"] >= 1, "админка отдаёт сводку")

    print("\nВсё ок. Время:", time.strftime("%H:%M:%S"))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("\nFAIL:", exc)
        raise SystemExit(1)
