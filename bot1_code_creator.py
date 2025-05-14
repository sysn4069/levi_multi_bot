import os
import json
import random
import string
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, filters
import nest_asyncio

nest_asyncio.apply()

TOKEN = os.getenv("BOT1_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
DB_PATH = "/data/referral_db.json"
CONFIG_PATH = "/data/config.json"

print("🚀 BOT1 시작됨")

def load_db():
    if not os.path.exists(DB_PATH):
        return {"referrals": {}, "codes": {}, "counts": {}}
    with open(DB_PATH, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_PATH, "w") as f:
        json.dump(data, f)

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {
            "group_link": "https://t.me/levi_group",
            "join_message": "👥 Levi 그룹에 참여하려면 아래 링크를 클릭하세요:"
        }
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f)

config = load_config()

def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

async def start1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    db = load_db()

    if context.args:
        ref_code = context.args[0]
        if ref_code in db.get("codes", {}):
            referrer_id = db["codes"][ref_code]
            if referrer_id != user_id:
                db["counts"][referrer_id] = db["counts"].get(referrer_id, 0) + 1
                save_db(db)

    await update.effective_message.reply_text(
        f"""{config['join_message']}
{config['group_link']}"""
    )

async def code1(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    bot_username = context.bot.username
    invite_link = f"https://t.me/{bot_username}?start={code}"
    await update.effective_message.reply_text(f"""📮 당신의 추천코드 링크:
{invite_link}""")

async def rank1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    counts = db.get("counts", {})
    if not counts:
        await update.effective_message.reply_text("📉 아직 추천 내역이 없습니다.")
        return
    sorted_users = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    msg = "🏆 추천 랭킹:\n"
    for i, (user_id, count) in enumerate(sorted_users, 1):
        msg += f"{i}위 - {count}회 추천\n"
    await update.effective_message.reply_text(msg)

async def reset1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        await update.effective_message.reply_text("⛔ 관리자만 사용할 수 있습니다.")
        return
    db = load_db()
    db["counts"] = {}
    save_db(db)
    await update.effective_message.reply_text("✅ 추천 기록이 초기화되었습니다.")

async def setlink1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        await update.effective_message.reply_text("⛔ 관리자만 변경할 수 있습니다.")
        return
    new_link = " ".join(context.args)
    config["group_link"] = new_link
    save_config(config)
    await update.effective_message.reply_text("✅ 그룹 링크가 변경되었습니다.")

async def setmsg1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        await update.effective_message.reply_text("⛔ 관리자만 변경할 수 있습니다.")
        return
    new_msg = " ".join(context.args)
    config["join_message"] = new_msg
    save_config(config)
    await update.effective_message.reply_text("✅ 입장 메시지가 변경되었습니다.")

async def info1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        f"""📎 현재 그룹 링크: {config['group_link']}
📝 입장 메시지: {config['join_message']}"""
    )

def safe_main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler(["start", "start1"], start1))
    app.add_handler(CommandHandler("code1", code1))
    app.add_handler(CommandHandler("rank1", rank1))
    app.add_handler(CommandHandler("reset1", reset1))
    app.add_handler(CommandHandler("setlink1", setlink1))
    app.add_handler(CommandHandler("setmsg1", setmsg1))
    app.add_handler(CommandHandler("info1", info1))
    await app.run_polling()

if __name__ == "__main__":
    safe_main()
