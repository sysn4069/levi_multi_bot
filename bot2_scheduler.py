import os
import json
import asyncio
import nest_asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

nest_asyncio.apply()

TOKEN = os.getenv("BOT2_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")  # 단일 관리자 ID

# 저장 경로
os.makedirs("/mnt/data", exist_ok=True)
SETTINGS_PATH = "/mnt/data/schedule_settings.json"

print("🚀 BOT2 시작됨")

# 관리자 확인 함수
def is_admin(user_id: int) -> bool:
    return str(user_id) == ADMIN_ID

# 설정 로드 및 저장
def load_settings():
    if not os.path.exists(SETTINGS_PATH):
        return {"message": "", "interval": 60, "enabled": False}
    with open(SETTINGS_PATH, "r") as f:
        return json.load(f)

def save_settings(settings):
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f)

# /setmsg2 명령어
async def setmsg2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ 관리자만 사용 가능합니다.")
        return
    message = " ".join(context.args)
    if not message:
        await update.message.reply_text("❗ 사용법: /setmsg2 [전송할 메시지]")
        return
    settings = load_settings()
    settings["message"] = message
    save_settings(settings)
    await update.message.reply_text("✅ 전송할 메시지가 설정되었습니다.")

# /setinterval2 명령어
async def setinterval2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ 관리자만 사용 가능합니다.")
        return
    try:
        minutes = int(context.args[0])
        settings = load_settings()
        settings["interval"] = minutes
        save_settings(settings)
        await update.message.reply_text(f"✅ 메시지 전송 주기가 {minutes}분으로 설정되었습니다.")
    except:
        await update.message.reply_text("❗ 사용법: /setinterval2 [분]")

# /showsettings2 명령어
async def showsettings2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    settings = load_settings()
    msg = f"""🔧 현재 설정:
- 메시지: {settings.get("message", "")}
- 주기: {settings.get("interval", 60)}분
- 활성화 상태: {"✅ 활성화됨" if settings.get("enabled") else "⛔ 비활성화"}"""
    await update.message.reply_text(msg)

# 메시지 자동 전송 루프
async def auto_sender(app):
    while True:
        settings = load_settings()
        if settings.get("enabled") and settings.get("message"):
            try:
                await app.bot.send_message(chat_id=int(ADMIN_ID), text=settings["message"])
            except Exception as e:
                print(f"메시지 전송 오류: {e}")
        await asyncio.sleep(settings.get("interval", 60) * 60)

# /start2 명령어
async def start2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ 관리자만 사용 가능합니다.")
        return
    settings = load_settings()
    settings["enabled"] = True
    save_settings(settings)
    await update.message.reply_text("✅ 자동 메시지 전송이 시작되었습니다.")

# /stop2 명령어
async def stop2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ 관리자만 사용 가능합니다.")
        return
    settings = load_settings()
    settings["enabled"] = False
    save_settings(settings)
    await update.message.reply_text("🛑 자동 메시지 전송이 중단되었습니다.")

# 메인 함수
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("setmsg2", setmsg2))
    app.add_handler(CommandHandler("setinterval2", setinterval2))
    app.add_handler(CommandHandler("showsettings2", showsettings2))
    app.add_handler(CommandHandler("start2", start2))
    app.add_handler(CommandHandler("stop2", stop2))

    asyncio.create_task(auto_sender(app))
    print("✅ bot2_scheduler is running")
    await app.run_polling()

def safe_main():
    asyncio.run(main())

if __name__ == "__main__":
    safe_main()
