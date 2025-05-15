import os
import json
import asyncio
import sqlite3
import datetime
import hashlib
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import nest_asyncio

nest_asyncio.apply()

TOKEN = os.getenv("BOT4_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
SHARE_API_URL = os.getenv("SHARE_API_URL", "https://your-api.com")
TRACK_URL = SHARE_API_URL + "/track"

VIDEO_DATA_PATH = "/mnt/data/video_data.json"
DB_PATH = "/mnt/data/clicks.db"
os.makedirs("/mnt/data", exist_ok=True)

# ---------- 데이터 로드/저장 ----------
def load_videos():
    if os.path.exists(VIDEO_DATA_PATH):
        with open(VIDEO_DATA_PATH, "r") as f:
            return json.load(f)
    return {}

def save_videos(data):
    with open(VIDEO_DATA_PATH, "w") as f:
        json.dump(data, f)

# ---------- 고정된 video_id 생성 ----------
def generate_video_id(title: str) -> str:
    return hashlib.sha256(title.encode()).hexdigest()[:10]

# ---------- DB 초기화 ----------
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

# ---------- 관리자 확인 ----------
def is_admin(update: Update) -> bool:
    return str(update.effective_user.id) == ADMIN_ID

# ---------- 명령어 핸들러들 ----------
async def register_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ 관리자만 사용할 수 있습니다.")
        return
    try:
        text = " ".join(context.args)
        title, video_url, thumbnail = [s.strip() for s in text.split("|")]
    except Exception:
        await update.message.reply_text("❗ 형식: /register4 제목 | 영상URL | 썸네일URL")
        return
    video_id = generate_video_id(title)
    videos = load_videos()
    videos[video_id] = {
        "title": title,
        "video_url": video_url,
        "thumbnail": thumbnail,
        "count": 0
    }
    save_videos(videos)

    # --- API 서버에 동기화 ---
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                SHARE_API_URL + "/api/sync_video",
                json={
                    "video_id": video_id,
                    "title": title,
                    "video_url": video_url,
                    "thumbnail": thumbnail
                }
            )
    except Exception as e:
        print(f"❌ API 동기화 실패: {e}")

    await update.message.reply_text(f"✅ 등록 완료\n영상ID: {video_id}", parse_mode='Markdown')

async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ 형식: /getlink4 영상ID")
        return
    video_id = context.args[0]
    user_id = str(update.effective_user.id)
    share_link = f"{TRACK_URL}?vid={video_id}&uid={user_id}"
    await update.message.reply_text(f"🔗 당신의 공유 링크:\n{share_link}")

async def list_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    videos = load_videos()
    if not videos:
        await update.message.reply_text("📂 등록된 영상이 없습니다.")
        return
    msg = "📋 등록된 영상 목록:\n"
    for vid, info in videos.items():
        msg += f"- {info.get('title')} (ID: `{vid}`)\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def delete_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("❌ 관리자만 사용할 수 있습니다.")
        return
    if not context.args:
        await update.message.reply_text("❗ 삭제할 영상 ID를 입력해주세요.")
        return
    video_id = context.args[0]
    videos = load_videos()
    if video_id in videos:
        del videos[video_id]
        save_videos(videos)
        await update.message.reply_text(f"🗑️ 영상 {video_id} 삭제 완료")
    else:
        await update.message.reply_text("⚠️ 영상 ID 없음")

async def edit_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("❌ 관리자만 사용할 수 있습니다.")
        return
    parts = " ".join(context.args).split("|")
    if len(parts) < 2:
        await update.message.reply_text("❗ 형식: /editvideo4 영상ID | 제목 | 썸네일URL(선택) | 영상URL(선택)")
        return
    video_id = parts[0].strip()
    title = parts[1].strip()
    thumbnail = parts[2].strip() if len(parts) > 2 else None
    video_url = parts[3].strip() if len(parts) > 3 else None
    videos = load_videos()
    if video_id not in videos:
        await update.message.reply_text("⚠️ 영상 ID 없음")
        return
    videos[video_id]["title"] = title
    if thumbnail:
        videos[video_id]["thumbnail"] = thumbnail
    if video_url:
        videos[video_id]["video_url"] = video_url
    save_videos(videos)
    await update.message.reply_text("✅ 영상 정보 수정 완료")

async def mystats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM clicks WHERE uid = ?", (user_id,))
    count = c.fetchone()[0]
    conn.close()
    await update.message.reply_text(f"📊 현재까지 {count}명이 당신의 링크를 클릭했습니다.")

async def show_rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT uid, COUNT(*) as cnt FROM clicks GROUP BY uid ORDER BY cnt DESC")
    rows = c.fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("🏎️ 아직 클릭 데이터가 없습니다.")
        return
    msg = "🏆 공유 랭킹:\n"
    for i, (uid, count) in enumerate(rows, 1):
        msg += f"{i}. 유저 {uid} - {count}회\n"
    await update.message.reply_text(msg)

async def reset_clicks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ 관리자만 사용할 수 있습니다.")
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM clicks")
    conn.commit()
    conn.close()
    await update.message.reply_text("✅ 클릭 데이터가 초기화되었습니다.")

# ---------- 실행 ----------
async def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("register4", register_video))
    app.add_handler(CommandHandler("getlink4", get_link))
    app.add_handler(CommandHandler("listvideos4", list_videos))
    app.add_handler(CommandHandler("deletevideo4", delete_video))
    app.add_handler(CommandHandler("editvideo4", edit_video))
    app.add_handler(CommandHandler("mystats4", mystats))
    app.add_handler(CommandHandler("rank4", show_rank))
    app.add_handler(CommandHandler("reset4", reset_clicks))
    print("✅ bot4_share_tracker (local+sqlite+sync) is running")
    await app.run_polling()

def safe_main():
    asyncio.run(main())

if __name__ == "__main__":
    safe_main()
