import os
import json
import asyncio
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, filters
import nest_asyncio

nest_asyncio.apply()

TOKEN = os.getenv("BOT4_TOKEN")
API_BASE_URL = os.getenv("SHARE_API_URL")  # 예: "https://your-api-server.onrender.com"
ADMIN_IDS = os.getenv("ADMIN_IDS", "").split(",")

def is_admin(update: Update) -> bool:
    return str(update.effective_user.id) in ADMIN_IDS

# /register4
async def register_video4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ 관리자만 사용할 수 있습니다.")
        return
    try:
        text = " ".join(context.args)
        title, thumbnail = [s.strip() for s in text.split("|")]
    except Exception:
        await update.message.reply_text("❗ 형식: /register4 제목 | 썸네일URL")
        return

    video_id = str(hash(title))
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

# /getlink4
async def get_link4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        video_id = context.args[0]
        user_id = str(update.effective_user.id)
        share_link = f"{API_BASE_URL}/track?video_id={video_id}&user_id={user_id}"
        await update.message.reply_text(f"🔗 당신의 공유 링크:\n{share_link}")
    except IndexError:
        await update.message.reply_text("❗ 형식: /getlink4 영상ID")

# /mystats4
async def my_stats4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{API_BASE_URL}/api/user_stats", params={"user_id": user_id})
    if res.status_code == 200:
        data = res.json()
        count = data.get("count", 0)
        await update.message.reply_text(f"📊 현재까지 {count}명이 당신의 링크를 클릭했습니다.")
    else:
        await update.message.reply_text("⚠️ 통계 조회 실패")

# /rank4
async def show_rank4(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

# /reset4
async def reset_clicks4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("❌ 관리자만 사용할 수 있는 명령어입니다.")
        return
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{API_BASE_URL}/api/reset_clicks")
    if res.status_code == 200:
        await update.message.reply_text("✅ 클릭 데이터가 초기화되었습니다.")
    else:
        await update.message.reply_text("⚠️ 초기화 실패")

# /deletevideo4
async def delete_video4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("❌ 관리자만 사용할 수 있는 명령어입니다.")
        return
    if not context.args:
        await update.message.reply_text("❗ 삭제할 영상 ID를 입력해주세요.")
        return
    video_id = context.args[0]
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{API_BASE_URL}/api/delete_video", json={"video_id": video_id})
    if res.status_code == 200:
        await update.message.reply_text(f"🗑️ 영상 `{video_id}` 삭제 완료")
    else:
        await update.message.reply_text("⚠️ 삭제 실패 또는 영상 ID 없음")

# /editvideo4
async def edit_video4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("❌ 관리자만 사용할 수 있는 명령어입니다.")
        return
    parts = " ".join(context.args).split("|")
    if len(parts) < 2:
        await update.message.reply_text("❗ 형식: /editvideo4 영상ID | 제목 | 썸네일URL(선택)")
        return
    video_id = parts[0].strip()
    title = parts[1].strip()
    thumbnail = parts[2].strip() if len(parts) > 2 else None
    payload = {"video_id": video_id, "title": title}
    if thumbnail:
        payload["thumbnail"] = thumbnail

    async with httpx.AsyncClient() as client:
        res = await client.post(f"{API_BASE_URL}/api/edit_video", json=payload)
    if res.status_code == 200:
        await update.message.reply_text("✅ 영상 정보 수정 완료")
    else:
        await update.message.reply_text("⚠️ 수정 실패 또는 영상 ID 없음")

# 메인
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("register4", register_video4, filters=filters.ALL))
    app.add_handler(CommandHandler("getlink4", get_link4, filters=filters.ALL))
    app.add_handler(CommandHandler("mystats4", my_stats4, filters=filters.ALL))
    app.add_handler(CommandHandler("rank4", show_rank4, filters=filters.ALL))
    app.add_handler(CommandHandler("reset4", reset_clicks4, filters=filters.ALL))  # ✅ 바뀐 부분
    app.add_handler(CommandHandler("deletevideo4", delete_video4, filters=filters.ALL))
    app.add_handler(CommandHandler("editvideo4", edit_video4, filters=filters.ALL))

    print("✅ bot4_share_tracker is running...")
    await app.run_polling()

def safe_main():
    asyncio.run(main())

if __name__ == "__main__":
    safe_main()
