from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel
import sqlite3
import datetime
import os
import json

app = FastAPI()

# 로컬 경로로 변경 (Starter 플랜에서는 'mnt/data'로 해야 함)
DATA_DIR = "mnt/data"
DATA_PATH = os.path.join(DATA_DIR, "video_data.json")
DB_PATH = os.path.join(DATA_DIR, "clicks.db")

os.makedirs(DATA_DIR, exist_ok=True)

# ---------- 데이터 처리 ----------
def load_data():
    if not os.path.exists(DATA_PATH):
        return {"videos": {}}
    with open(DATA_PATH, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_PATH, "w") as f:
        json.dump(data, f)

# ---------- DB 초기화 ----------
def init_db():
    try:
        with open(DB_PATH, "a"):
            pass  # Ensure we can write to the DB file
    except Exception as e:
        print(f"❌ [init_db 오류] DB 파일 생성 실패: {e}")
        raise SystemExit("⛔ DB 파일 생성 실패. 경로를 확인하세요.")

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

# ---------- 공유 링크 클릭 ----------
@app.get("/track")
async def track(vid: str, uid: str, request: Request):
    ip = request.client.host
    today = datetime.datetime.utcnow().date().isoformat()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO clicks (vid, uid, ip, date) VALUES (?, ?, ?, ?)", (vid, uid, ip, today))
        conn.commit()
        status = "counted"
    except sqlite3.IntegrityError:
        status = "duplicate"
    conn.close()

    data = load_data()
    video_url = data.get("videos", {}).get(vid, {}).get("video_url")
    if video_url:
        return RedirectResponse(video_url)

    return JSONResponse(content={"status": status, "message": "영상 링크가 없습니다."})

# ---------- 봇에서 영상 등록 시 동기화용 ----------
class VideoData(BaseModel):
    video_id: str
    title: str
    video_url: str
    thumbnail: str

@app.post("/api/sync_video")
async def sync_video(data: VideoData):
    all_data = load_data()
    all_data.setdefault("videos", {})[data.video_id] = {
        "title": data.title,
        "video_url": data.video_url,
        "thumbnail": data.thumbnail,
        "count": 0
    }
    save_data(all_data)
    return {"status": "ok", "message": f"영상 {data.video_id} 동기화 완료"}

# ---------- 시작 ----------
init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=10000)
