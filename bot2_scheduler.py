import os
import json
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    Application,
    CommandHandler,
    ContextTypes,
    filters,
)
import nest_asyncio

nest_asyncio.apply()

TOKEN = os.getenv("BOT2_TOKEN")
SETTINGS_PATH = "bot2_settings.json"
DEFAULT_INTERVAL = 60  # minutes

config = {
    "chat_id": None,
    "message": "기본 메시지입니다.",
    "interval": DEFAULT_INTERVAL,
    "enabled": False
}

def load_settings():
    if os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, "r") as f:
            config.update(json.load(f))

def save_settings():
    with open(SETTINGS_PATH, "w") as f:
        json.dump(config, f)

async def set_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if not text:
        await update.effective_message.reply_text("❗ 메시지를 입력해주세요.")
        return
    config["message"] = text
    save_settings()
    await update.effective_message.reply_text(f"✅ 메시지가 설정되었습니다: {text}")

async def set_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        minutes = int(context.args[0])
        config["interval"] = minutes
        save_settings()
        await update.effective_message.reply_text(f"⏱️ 전송 간격이 {minutes}분으로 설정되었습니다.")
    except (IndexError, ValueError):
        await update.effective_message.reply_text("❗ 숫자로 된 간격(분)을 입력해주세요. 예: /setinterval 30")

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = f"""📋 현재 설정:
메시지: {config['message']}
간격: {config['interval']}분
활성화: {"✅" if config["enabled"] else "❌"}"""
    await update.effective_message.reply_text(msg)

async def start_sending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    config["chat_id"] = chat_id
    config["enabled"] = True
    save_settings()
    await update.effective_message.reply_text("🚀 자동 메시지 전송이 시작되었습니다.")

async def stop_sending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config["enabled"] = False
    save_settings()
    await update.effective_message.reply_text("🛑 자동 메시지 전송이 중단되었습니다.")

# ✅ 백그라운드 루프
async def background_loop(app: Application):
    await app.wait_until_ready()
    while True:
        await asyncio.sleep(config["interval"] * 60)
        if config["enabled"] and config["chat_id"]:
            try:
                await app.bot.send_message(chat_id=config["chat_id"], text=config["message"])
            except Exception as e:
                print("메시지 전송 오류:", e)

# ✅ 메인
async def main():
    load_settings()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("setmsg", set_message))
    app.add_handler(CommandHandler("setinterval", set_interval))
    app.add_handler(CommandHandler("showsettings", show_settings))
    app.add_handler(CommandHandler("start", start_sending))
    app.add_handler(CommandHandler("stop", stop_sending))

    # ⛔ run_polling 전에 create_task 하지 말고...
    async def runner():
        asyncio.create_task(background_loop(app))  # ✅ 이 시점이면 앱은 이미 실행 중이라 경고 없음
        await app.run_polling()

    await runner()

def safe_main():
    asyncio.run(main())

if __name__ == "__main__":
    safe_main()
