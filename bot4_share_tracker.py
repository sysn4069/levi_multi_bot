import os
import json
import asyncio
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, filters
import nest_asyncio

nest_asyncio.apply()

TOKEN = os.getenv("BOT4_TOKEN")
API_BASE_URL = os.getenv("SHARE_API_URL")  # 예: "https://your-api-server.com"

ADMIN_IDS = os.getenv("ADMIN_IDS", "").split(",")

# /register 명령어 (관리자 전용)
async def register_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) not in ADMIN_IDS:
        await update.message.reply_text("⛔ 관리자만 사용할 수 있습니다.")
        return

    try:
        text = " ".join(context.args)
        title, thumbnail = [s.strip() for s in text.split("|")]
    except Exception:
        await update.message.reply_text("❗ 형식: /register 영상제목 | 썸네일URL")
        return

    video_id = str(hash(title))  # 간단한 해시로 영상 ID 생성

    async with httpx.AsyncClient() as client:
        res = await client.post(f"{API_BASE_URL}/api/register", json={
            "video_id": video_id,
            "title": title,
            "thumbnail": thumbnail
        })

    if res.status_code == 200:
        await update.message.reply_text(f"✅ 등록 완료\n영상ID: `{video_id}`", parse_mode='Markdown')
    else:
        await update.message.reply_text("⚠️ 등록 실패")

# /getlink 명령어
async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        video_id = context.args[0]
        user_id = str(update.effective_user.id)
        share_link = f"{API_BASE_URL}/track?video_id={video_id}&user_id={user_id}"
        await update.message.reply_text(f"🔗 당신의 공유 링크:\n{share_link}")
    except IndexError:
        await update.message.reply_text("❗ 형식: /getlink 영상ID")

# /mystats 명령어
async def my_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{API_BASE_URL}/api/user_stats", params={"user_id": user_id})
    if res.status_code == 200:
        data = res.json()
        count = data.get("count", 0)
        await update.message.reply_text(f"📊 현재까지 {count}명이 당신의 링크를 클릭했습니다.")
    else:
        await update.message.reply_text("⚠️ 통계 조회 실패")

# /rank 명령어
async def show_rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{API_BASE_URL}/api/ranking")
    if res.status_code == 200:
        data = res.json()
        if not data:
            await update.message.reply_text("🏁 아직 클릭 데이터가 없습니다.")
            return
        msg = "🏆 공유 랭킹:\n"
        for i, (uid, count) in enumerate(data.items(), 1):
            msg += f"{i}. 유저 {uid} - {count}회\n"
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("⚠️ 랭킹 조회 실패")

# 메인 함수
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("register", register_video, filters=filters.ALL))
    app.add_handler(CommandHandler("getlink", get_link, filters=filters.ALL))
    app.add_handler(CommandHandler("mystats", my_stats, filters=filters.ALL))
    app.add_handler(CommandHandler("rank", show_rank, filters=filters.ALL))

    print("✅ bot4_share_tracker is running")
    await app.run_polling()

def safe_main():
    asyncio.run(main())

if __name__ == "__main__":
    safe_main()

# 관리자용 명령어 추가 (bot4_share_tracker.py 내부)

from telegram.ext import CommandHandler
from telegram import Update
from telegram.ext import ContextTypes

# 관리자 ID를 환경변수나 상수로 설정
ADMIN_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "123456789"))  # 예시

async def is_admin(update: Update):
    return update.effective_user and update.effective_user.id == ADMIN_ID

# /resetclicks4 명령어 - 클릭 데이터 초기화
async def reset_clicks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        await update.message.reply_text("❌ 관리자만 사용할 수 있는 명령어입니다.")
        return

    db = load_db()
    db["clicks"] = {}
    save_db(db)
    await update.message.reply_text("✅ 클릭 데이터가 초기화되었습니다.")

# /deletevideo [영상ID] 명령어
async def delete_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        await update.message.reply_text("❌ 관리자만 사용할 수 있는 명령어입니다.")
        return

    if not context.args:
        await update.message.reply_text("❗ 삭제할 영상 ID를 입력해주세요.")
        return

    vid = context.args[0]
    db = load_db()
    if vid in db["videos"]:
        del db["videos"][vid]
        save_db(db)
        await update.message.reply_text(f"🗑️ 영상 `{vid}` 이(가) 삭제되었습니다.")
    else:
        await update.message.reply_text("❗ 해당 영상 ID를 찾을 수 없습니다.")

# /editvideo [영상ID] | [새 제목] | [새 썸네일URL] 명령어
async def edit_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        await update.message.reply_text("❌ 관리자만 사용할 수 있는 명령어입니다.")
        return

    parts = " ".join(context.args).split("|")
    if len(parts) < 2:
        await update.message.reply_text("❗ 형식: /editvideo [영상ID] | [제목] | [썸네일URL] (썸네일은 선택)")
        return

    vid = parts[0].strip()
    title = parts[1].strip()
    thumbnail = parts[2].strip() if len(parts) > 2 else None

    db = load_db()
    if vid in db["videos"]:
        db["videos"][vid]["title"] = title
        if thumbnail:
            db["videos"][vid]["thumbnail"] = thumbnail
        save_db(db)
        await update.message.reply_text("✅ 영상 정보가 수정되었습니다.")
    else:
        await update.message.reply_text("❗ 해당 영상 ID를 찾을 수 없습니다.")

# 핸들러 등록 예시 (Application 객체에 연결)
app.add_handler(CommandHandler("resetclicks4", reset_clicks))
app.add_handler(CommandHandler("deletevideo", delete_video))
app.add_handler(CommandHandler("editvideo", edit_video))
