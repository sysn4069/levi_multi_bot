import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

print("🚀 BOT1 시작됨")

TOKEN = os.getenv("BOT1_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("추천코드봇이 시작되었습니다.")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    await app.run_polling()

def safe_main():
    asyncio.run(main())
