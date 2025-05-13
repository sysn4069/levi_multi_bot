
import os
import json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from datetime import datetime
from hashlib import sha256

app = FastAPI()

DB_FILE = "share_db.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"videos": {}, "clicks": {}}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

@app.post("/api/register")
async def register_video(req: Request):
    data = await req.json()
    video_id = data.get("video_id")
    title = data.get("title")
    thumbnail = data.get("thumbnail")

    if not video_id or not title:
        return JSONResponse(content={"error": "Missing video_id or title"}, status_code=400)

    db = load_db()
    db["videos"][video_id] = {"title": title, "thumbnail": thumbnail, "created": datetime.utcnow().isoformat()}
    save_db(db)
    return {"status": "ok"}

@app.get("/api/click")
async def count_click(video_id: str, user_id: str, ip: str):
    db = load_db()
    key = f"{video_id}:{ip}"

    if key in db["clicks"]:
        return {"status": "ignored", "reason": "already counted"}

    db["clicks"][key] = {"user_id": user_id, "timestamp": datetime.utcnow().isoformat()}
    save_db(db)
    return {"status": "counted"}

@app.get("/api/stats")
async def get_stats():
    db = load_db()
    counts = {}
    for key, val in db["clicks"].items():
        uid = val["user_id"]
        counts[uid] = counts.get(uid, 0) + 1
    return counts
