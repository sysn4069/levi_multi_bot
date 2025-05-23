import os
import json
import random
import string
import asyncio
import time
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import nest_asyncio

nest_asyncio.apply()

TOKEN = os.getenv("BOT1_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
API_URL = os.getenv("API_URL", "https://your-api-server.onrender.com/api/save_recommend")
DB_PATH = "/mnt/data/referral_db.json"
CONFIG_PATH = "/mnt/data/config.json"

print("🚀 BOT1 시작됨")

# ---------- 데이터 로딩 ----------
def load_db():
    if not os.path.exists(DB_PATH):
        return {"referrals": {}, "codes": {}, "counts": {}}
    with open(DB_PATH, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_PATH, "w") as f:
        json.dump(data, f)

def load_config():
    default = {
        "group_link": "https://t.me/levi_group",
        "channel_link": "https://t.me/levi_channel",
        "join_message": "👋 Levi 커뮤니티에 오신 걸 환영합니다!\n아래 버튼을 눌러 참여해주세요!"
    }
    if not os.path.exists(CONFIG_PATH):
        return default
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
        for key in default:
            if key not in config:
                config[key] = default[key]
        return config

def save_config(data):
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f)

# ---------- 추천 코드 생성 ----------
def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# ---------- 명령어 핸들러 ----------
async def start1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    db = load_db()
    config = load_config()

    # 추천 코드 추적
    if context.args:
        ref_code = context.args[0]
        if ref_code in db.get("codes", {}):
            referrer_id = db["codes"][ref_code]
            if referrer_id != user_id:
                db["counts"][referrer_id] = db["counts"].get(referrer_id, 0) + 1
                save_db(db)

    # 메시지 + 버튼
   message_text = (
    f"{config['join_message']}\n\n"
    "📢 공지채널 : 랩소디 공지방\n"
    "💬 소통방 : 랩소디 소통방"
)
   keyboard = [
    [
        InlineKeyboardButton("랩소디 공지방", url=config["channel_link"]),
        InlineKeyboardButton("랩소디 소통방", url=config["group_link"])
    ]
]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.effective_message.reply_text(message_text, reply_markup=reply_markup)

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
        try:
            requests.post(API_URL, json={
                "user_id": user_id,
                "code": code,
                "timestamp": time.time()
            })
        except Exception as e:
            print(f"[API 오류] 추천코드 저장 실패: {e}")

    bot_username = context.bot.username
    invite_link = f"https://t.me/{bot_username}?start={code}"
    await update.effective_message.reply_text(f"📮 당신의 추천코드 링크:\n{invite_link}")

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
    config = load_config()
    config["group_link"] = new_link
    save_config(config)
    await update.effective_message.reply_text("✅ 그룹 링크가 변경되었습니다.")

async def setchannel1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        await update.effective_message.reply_text("⛔ 관리자만 변경할 수 있습니다.")
        return
    new_link = " ".join(context.args)
    config = load_config()
    config["channel_link"] = new_link
    save_config(config)
    await update.effective_message.reply_text("✅ 채널 링크가 변경되었습니다.")

async def setmsg1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        await update.effective_message.reply_text("⛔ 관리자만 변경할 수 있습니다.")
        return
    new_msg = " ".join(context.args)
    config = load_config()
    config["join_message"] = new_msg
    save_config(config)
    await update.effective_message.reply_text("✅ 입장 메시지가 변경되었습니다.")

async def info1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = load_config()
    await update.effective_message.reply_text(
        f"""📎 그룹 링크: {config['group_link']}
📢 채널 링크: {config['channel_link']}
📝 입장 메시지: {config['join_message']}"""
    )

# ---------- 실행 ----------
def safe_main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

async def main():
    os.makedirs("/mnt/data", exist_ok=True)
    global DB_PATH, CONFIG_PATH
    DB_PATH = "/mnt/data/referral_db.json"
    CONFIG_PATH = "/mnt/data/config.json"
    load_config()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler(["start", "start1"], start1))
    app.add_handler(CommandHandler("code1", code1))
    app.add_handler(CommandHandler("rank1", rank1))
    app.add_handler(CommandHandler("reset1", reset1))
    app.add_handler(CommandHandler("setlink1", setlink1))
    app.add_handler(CommandHandler("setchannel1", setchannel1))
    app.add_handler(CommandHandler("setmsg1", setmsg1))
    app.add_handler(CommandHandler("info1", info1))
    await app.run_polling()

if __name__ == "__main__":
    safe_main()
