import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

print("🚀 BOT5 시작됨")

TOKEN = os.getenv("BOT5_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("이모지 이벤트봇이 시작되었습니다.")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    await app.run_polling()

def safe_main():
    asyncio.run(main())
