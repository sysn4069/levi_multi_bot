import os
import json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from datetime import datetime

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
    db["videos"][video_id] = {
        "title": title,
        "thumbnail": thumbnail,
        "created": datetime.utcnow().isoformat()
    }
    save_db(db)
    return {"status": "ok"}

@app.get("/track")
async def count_click(video_id: str, user_id: str, ip: str = ""):
    ip = ip or "unknown"
    db = load_db()
    key = f"{video_id}:{ip}"

    if key in db["clicks"]:
        return {"status": "ignored", "reason": "already counted"}

    db["clicks"][key] = {
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    save_db(db)
    return {"status": "counted"}

@app.get("/api/user_stats")
async def user_stats(user_id: str):
    db = load_db()
    count = sum(1 for entry in db["clicks"].values() if entry["user_id"] == user_id)
    return {"count": count}

@app.get("/api/ranking")
async def get_ranking():
    db = load_db()
    ranking = {}
    for entry in db["clicks"].values():
        uid = entry["user_id"]
        ranking[uid] = ranking.get(uid, 0) + 1
    sorted_ranking = dict(sorted(ranking.items(), key=lambda item: item[1], reverse=True))
    return sorted_ranking

@app.post("/api/reset_clicks")
async def reset_clicks():
    db = load_db()
    db["clicks"] = {}
    save_db(db)
    return {"status": "reset"}

@app.post("/api/delete_video")
async def delete_video(req: Request):
    data = await req.json()
    video_id = data.get("video_id")

    if not video_id:
        return JSONResponse(content={"error": "Missing video_id"}, status_code=400)

    db = load_db()
    if video_id in db["videos"]:
        del db["videos"][video_id]
        save_db(db)
        return {"status": "deleted"}
    return JSONResponse(content={"error": "Video not found"}, status_code=404)

@app.post("/api/edit_video")
async def edit_video(req: Request):
    data = await req.json()
    video_id = data.get("video_id")
    title = data.get("title")
    thumbnail = data.get("thumbnail")

    if not video_id or not title:
        return JSONResponse(content={"error": "Missing video_id or title"}, status_code=400)

    db = load_db()
    if video_id in db["videos"]:
        db["videos"][video_id]["title"] = title
        if thumbnail:
            db["videos"][video_id]["thumbnail"] = thumbnail
        save_db(db)
        return {"status": "updated"}
    return JSONResponse(content={"error": "Video not found"}, status_code=404)
