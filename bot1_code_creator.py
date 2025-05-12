import os
import json
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT1_TOKEN")
DB_PATH = "referral_db.json"

print("🚀 BOT1 시작됨")

def load_db():
    if not os.path.exists(DB_PATH):
        return {"referrals": {}, "codes": {}}
    with open(DB_PATH, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_PATH, "w") as f:
        json.dump(data, f)

def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    db = load_db()

    if user_id in db["referrals"]:
        code = db["referrals"][user_id]
    else:
        code = generate_code()
        while code in db["codes"]:  # 중복 방지
            code = generate_code()
        db["referrals"][user_id] = code
        db["codes"][code] = user_id
        save_db(db)

    await update.message.reply_text(f"✅ 추천 등록 완료!\n📮 당신의 추천코드: `{code}`", parse_mode="Markdown")

def safe_main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    await app.run_polling()
