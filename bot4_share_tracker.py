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
