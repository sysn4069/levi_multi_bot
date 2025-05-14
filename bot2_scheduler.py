import os
import json
import asyncio
import nest_asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

nest_asyncio.apply()

TOKEN = os.getenv("BOT2_TOKEN")
ADMIN_IDS = os.getenv("ADMIN_IDS", "").split(",")

# 경로 설정
os.makedirs("/mnt/data", exist_ok=True)
DB_PATH = "/mnt/data/schedule_data.json"

print("🚀 BOT2 시작됨")

# 관리자 확인
def is_admin(user_id: int) -> bool:
    return str(user_id) in ADMIN_IDS

# 스케줄 데이터 로드 및 저장
def load_data():
    if not os.path.exists(DB_PATH):
        return {}
    with open(DB_PATH, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DB_PATH, "w") as f:
        json.dump(data, f)

# 명령어: /addmsg2 시간 메시지
async def addmsg2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ 관리자만 사용할 수 있습니다.")
        return

    try:
        hour = context.args[0]
        message = " ".join(context.args[1:])
        data = load_data()
        data[hour] = message
        save_data(data)
        await update.message.reply_text(f"✅ {hour}시에 보낼 메시지가 추가되었습니다.")
    except:
        await update.message.reply_text("❗ 사용법: /addmsg2 시간 메시지")

# 명령어: /listmsg2
async def listmsg2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data:
        await update.message.reply_text("📭 등록된 메시지가 없습니다.")
    else:
        msg = "📋 등록된 메시지 목록:\n"
        for hour, text in sorted(data.items()):
            msg += f"{hour}: {text}\n"
        await update.message.reply_text(msg)

# 명령어: /delmsg2 시간
async def delmsg2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ 관리자만 사용할 수 있습니다.")
        return

    try:
        hour = context.args[0]
        data = load_data()
        if hour in data:
            del data[hour]
            save_data(data)
            await update.message.reply_text(f"🗑️ {hour}시 메시지가 삭제되었습니다.")
        else:
            await update.message.reply_text("❌ 해당 시간에 메시지가 없습니다.")
    except:
        await update.message.reply_text("❗ 사용법: /delmsg2 시간")

# 메시지 자동 전송 루프 (예시 목적, 실제 구현 미완)
async def send_scheduled_messages(app):
    while True:
        # 실제 사용시 시간 체크 및 전송 로직 구현 필요
        await asyncio.sleep(60)

# 메인 함수
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("addmsg2", addmsg2))
    app.add_handler(CommandHandler("listmsg2", listmsg2))
    app.add_handler(CommandHandler("delmsg2", delmsg2))

    asyncio.create_task(send_scheduled_messages(app))

    print("✅ bot2_scheduler is running")
    await app.run_polling()

def safe_main():
    asyncio.run(main())

if __name__ == "__main__":
    safe_main()
