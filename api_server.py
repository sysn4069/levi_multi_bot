from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
import sqlite3
import datetime
import os
import json

app = FastAPI()

DATA_PATH = "/mnt/data/video_data.json"
DB_PATH = "/mnt/data/clicks.db"
os.makedirs("/mnt/data", exist_ok=True)

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

    video_url = load_data()["videos"].get(vid, {}).get("video_url")
    if video_url:
        return RedirectResponse(video_url)

    return JSONResponse(content={"status": status, "message": "영상 링크가 없습니다."})

init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=10000)
