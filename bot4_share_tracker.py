from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
import sqlite3
import datetime
import os
import json
import uuid

app = FastAPI()

DATA_PATH = "video_data.json"
DB_PATH = "clicks.db"
RECOMMEND_PATH = "/mnt/data/recommendations.json"

def load_data():
    if not os.path.exists(DATA_PATH):
        return {"videos": {}}
    with open(DATA_PATH, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_PATH, "w") as f:
        json.dump(data, f)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS clicks (
            vid TEXT,
            uid TEXT,
            ip TEXT,
            date TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(vid, uid, ip, date)
        )
    ''')
    conn.commit()
    conn.close()

@app.get("/track")
async def track(vid: str, uid: str, request: Request):
    ip = request.client.host
    today = datetime.datetime.utcnow().date().isoformat()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO clicks (vid, uid, ip, date) VALUES (?, ?, ?, ?)", (vid, uid, ip, today))
        conn.commit()
        data = load_data()
        if vid in data["videos"]:
            data["videos"][vid]["count"] += 1
            save_data(data)
        status = "counted"
    except sqlite3.IntegrityError:
        status = "duplicate"
    conn.close()

    video_url = data["videos"].get(vid, {}).get("video_url")
    if video_url:
        return RedirectResponse(video_url)

    return JSONResponse(content={"status": status, "message": "영상 링크가 없습니다."})

@app.post("/api/register")
async def register_video(request: Request):
    payload = await request.json()
    vid = str(uuid.uuid4())
    title = payload.get("title")
    thumbnail = payload.get("thumbnail")
    video_url = payload.get("video_url")

    if not title:
        return JSONResponse(content={"error": "Missing title"}, status_code=400)

    data = load_data()
    data["videos"][vid] = {
        "title": title,
        "thumbnail": thumbnail,
        "video_url": video_url,
        "count": 0
    }
    save_data(data)
    return {"status": "ok", "video_id": vid}

@app.get("/api/user_stats")
async def user_stats(user_id: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM clicks WHERE uid = ?", (user_id,))
    count = c.fetchone()[0]
    conn.close()
    return {"count": count}

@app.get("/api/ranking")
async def ranking():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT uid, COUNT(*) as cnt FROM clicks GROUP BY uid ORDER BY cnt DESC")
    rows = c.fetchall()
    conn.close()
    return {uid: cnt for uid, cnt in rows}

@app.post("/api/reset_clicks")
def reset_clicks():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM clicks")
    conn.commit()
    conn.close()
    return {"status": "reset"}

@app.post("/api/delete_video")
async def delete_video(request: Request):
    payload = await request.json()
    vid = payload.get("video_id")
    data = load_data()
    if vid in data["videos"]:
        del data["videos"][vid]
        save_data(data)
        return {"status": "deleted"}
    return JSONResponse(content={"error": "not found"}, status_code=404)

@app.post("/api/edit_video")
async def edit_video(request: Request):
    payload = await request.json()
    vid = payload.get("video_id")
    title = payload.get("title")
    thumbnail = payload.get("thumbnail")
    video_url = payload.get("video_url")

    data = load_data()
    if vid not in data["videos"]:
        return JSONResponse(content={"error": "not found"}, status_code=404)

    if title:
        data["videos"][vid]["title"] = title
    if thumbnail:
        data["videos"][vid]["thumbnail"] = thumbnail
    if video_url:
        data["videos"][vid]["video_url"] = video_url

    save_data(data)
    return {"status": "updated"}

@app.post("/api/save_recommend")
async def save_recommend(request: Request):
    payload = await request.json()
    user_id = str(payload.get("user_id"))
    code = payload.get("code")
    timestamp = payload.get("timestamp")

    if not os.path.exists(RECOMMEND_PATH):
        with open(RECOMMEND_PATH, "w") as f:
            json.dump({}, f)

    with open(RECOMMEND_PATH, "r") as f:
        data = json.load(f)

    data[user_id] = {
        "code": code,
        "timestamp": timestamp
    }

    with open(RECOMMEND_PATH, "w") as f:
        json.dump(data, f, indent=2)

    return {"status": "ok"}

init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=10000)
