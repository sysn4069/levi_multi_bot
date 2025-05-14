import os
import json
import asyncio
import nest_asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# 환경변수 및 경로
TOKEN = os.getenv("BOT5_TOKEN")
ADMIN_IDS = {int(os.getenv("ADMIN_ID", "0"))}
DATA_PATH = "render/data/bot5_event.json"
os.makedirs("render/data", exist_ok=True)

nest_asyncio.apply()

# 기본 구조
event_data = {
    "emoji_to_track": None,
    "participant_limit": None,
    "participants": [],
    "event_started": False
}

# 파일 불러오기 / 저장
def load_event_data():
    global event_data
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "r") as f:
            event_data = json.load(f)

def save_event_data():
    with open(DATA_PATH, "w") as f:
        json.dump(event_data, f)

# 관리자 확인
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# 명령어 핸들러들
async def start5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("이모지 선착순 이벤트 봇입니다.\n관리자는 /setemoji5, /setlimit5, /startevent5 명령으로 설정 후 시작하세요.")

async def setemoji(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if context.args:
        event_data["emoji_to_track"] = context.args[0]
        save_event_data()
        await update.message.reply_text(f"감지할 이모지가 '{event_data['emoji_to_track']}'로 설정되었습니다.")

async def setlimit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    try:
        limit = int(context.args[0])
        event_data["participant_limit"] = limit
        save_event_data()
        await update.message.reply_text(f"선착순 인원이 {limit}명으로 설정되었습니다.")
    except:
        await update.message.reply_text("❗ 숫자를 정확히 입력해주세요.")

async def start_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not event_data["emoji_to_track"] or not event_data["participant_limit"]:
        await update.message.reply_text("이모지와 인원 수를 먼저 설정하세요.")
        return
    event_data["event_started"] = True
    save_event_data()
    await update.message.reply_text("✅ 이벤트가 시작되었습니다! 설정된 이모지를 포함해 메시지를 보내면 참여됩니다.")

async def reset5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    event_data.update({
        "emoji_to_track": None,
        "participant_limit": None,
        "participants": [],
        "event_started": False
    })
    save_event_data()
    await update.message.reply_text("🔁 이벤트가 초기화되었습니다.")

async def list5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not event_data["participants"]:
        await update.message.reply_text("아직 참여자가 없습니다.")
        return
    lines = [f"{i+1}. {p['name']}" for i, p in enumerate(event_data["participants"])]
    await update.message.reply_text("👥 현재 참여자 목록:\n" + "\n".join(lines))

async def status5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if event_data["emoji_to_track"] and event_data["participant_limit"]:
        await update.message.reply_text(
            f"""📊 현재 이벤트 상태:
- 감지 이모지: {event_data['emoji_to_track']}
- 인원 제한: {event_data['participant_limit']}
- 현재 참여자 수: {len(event_data['participants'])}
- 이벤트 시작됨: {event_data['event_started']}"""
        )
    else:
        await update.message.reply_text("❗ 아직 이모지나 인원 수가 설정되지 않았습니다.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not event_data["event_started"] or not event_data["emoji_to_track"]:
        return

    text = update.message.text
    user_id = update.effective_user.id

    if event_data["emoji_to_track"] not in text:
        return

    if user_id in [p["id"] for p in event_data["participants"]]:
        return

    if len(event_data["participants"]) >= event_data["participant_limit"]:
        await update.message.reply_text("😥 이벤트가 마감되었습니다.")
        return

    event_data["participants"].append({
        "id": user_id,
        "name": update.effective_user.full_name
    })
    save_event_data()

    count = len(event_data["participants"])
    if count == event_data["participant_limit"]:
        await update.message.reply_text(f"{update.effective_user.full_name}님이 마지막 참여자입니다! ({count}/{event_data['participant_limit']})")
    else:
        await update.message.reply_text(f"{update.effective_user.full_name}님이 참여하셨습니다! ({count}/{event_data['participant_limit']})")

# 메인
async def main():
    load_event_data()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start5", start5))
    app.add_handler(CommandHandler("setemoji5", setemoji))
    app.add_handler(CommandHandler("setlimit5", setlimit))
    app.add_handler(CommandHandler("startevent5", start_event))
    app.add_handler(CommandHandler("reset5", reset5))
    app.add_handler(CommandHandler("list5", list5))
    app.add_handler(CommandHandler("status5", status5))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ bot5_emoji_event.py is running...")
    await app.run_polling()

def safe_main():
    asyncio.run(main())

if __name__ == "__main__":
    safe_main()
