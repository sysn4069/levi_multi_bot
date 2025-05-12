import os
import asyncio
import nest_asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

print("🚀 BOT2 시작됨")

nest_asyncio.apply()
TOKEN = os.getenv("BOT2_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("자동 메시지봇이 시작되었습니다.")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    await app.run_polling()

def safe_main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
