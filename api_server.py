from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import sqlite3
import datetime
import os
import json

app = FastAPI()
DATA_PATH = "video_data.json"
DB_PATH = "clicks.db"

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
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(vid, uid, ip, DATE(timestamp))
        )
    ''')
    conn.commit()
    conn.close()

@app.get("/track")
async def track(vid: str, uid: str, request: Request):
    ip = request.client.host
    now = datetime.datetime.now().isoformat()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO clicks (vid, uid, ip) VALUES (?, ?, ?)", (vid, uid, ip))
        conn.commit()
        # Count update
        data = load_data()
        if vid in data["videos"]:
            data["videos"][vid]["count"] += 1
            save_data(data)
        status = "counted"
    except sqlite3.IntegrityError:
        status = "duplicate"
    conn.close()
    return JSONResponse(content={"status": status})

init_db()