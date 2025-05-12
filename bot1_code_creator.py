
import os
import json
import random
import string
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT1_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
DB_PATH = "referral_db.json"

print("🚀 BOT1 시작됨")

def load_db():
    if not os.path.exists(DB_PATH):
        return {"referrals": {}, "codes": {}, "counts": {}}
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
        while code in db["codes"]:
            code = generate_code()
        db["referrals"][user_id] = code
        db["codes"][code] = user_id
        db["counts"][user_id] = 0
        save_db(db)

    await update.message.reply_text(
        f"✅ 추천 등록 완료!
📮 당신의 추천코드: `{code}`", parse_mode="Markdown"
    )

async def ranking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    counts = db.get("counts", {})
    if not counts:
        await update.message.reply_text("📉 아직 추천 내역이 없습니다.")
        return
    sorted_users = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    msg = "🏆 추천 랭킹:
"
    for i, (user_id, count) in enumerate(sorted_users, 1):
        msg += f"{i}위 - {count}회 추천
"
    await update.message.reply_text(msg)

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ 관리자만 사용할 수 있습니다.")
        return
    db = load_db()
    db["counts"] = {}
    save_db(db)
    await update.message.reply_text("✅ 추천 기록이 초기화되었습니다.")

def safe_main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("랭킹", ranking))
    app.add_handler(CommandHandler("초기화", reset))
    await app.run_polling()
