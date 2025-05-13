import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

ADMIN_IDS = set(map(int, os.getenv("ADMIN_IDS", "").split(",")))

emoji_to_track = None
participant_limit = None
participants = []
event_started = False

# 관리자 체크
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# 명령어: /start5
async def start5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("이모지 선착순 이벤트 봇입니다.\n관리자는 /setemoji, /setlimit, /start_event5 명령으로 설정 후 시작하세요.")

# 명령어: /setemoji 😍
async def setemoji(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("이 명령어는 관리자만 사용할 수 있습니다.")
        return
    global emoji_to_track
    if context.args:
        emoji_to_track = context.args[0]
    # 메시지는 출력하지 않음 (요청사항)

# 명령어: /setlimit 5
async def setlimit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("이 명령어는 관리자만 사용할 수 있습니다.")
        return
    global participant_limit
    if context.args:
        try:
            participant_limit = int(context.args[0])
            await update.message.reply_text(f"선착순 인원이 {participant_limit}명으로 설정되었습니다.")
        except ValueError:
            await update.message.reply_text("올바른 숫자를 입력해주세요.")

# 명령어: /start_event5
async def start_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("이 명령어는 관리자만 사용할 수 있습니다.")
        return
    global event_started
    if emoji_to_track is None or participant_limit is None:
        await update.message.reply_text("이모지와 인원 수가 모두 설정되어야 시작할 수 있습니다.")
        return
    event_started = True
    await update.message.reply_text("이벤트가 시작되었습니다! 설정된 이모지를 포함해 메시지를 보내면 참여됩니다.")

# 명령어: /reset5
async def reset5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("이 명령어는 관리자만 사용할 수 있습니다.")
        return
    global emoji_to_track, participant_limit, participants, event_started
    emoji_to_track = None
    participant_limit = None
    participants = []
    event_started = False
    await update.message.reply_text("이벤트 설정이 초기화되었습니다.")

# 명령어: /list5
async def list5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not participants:
        await update.message.reply_text("현재 참여자가 없습니다.")
    else:
        lines = [f"{i+1}. {p['name']}" for i, p in enumerate(participants)]
        await update.message.reply_text("현재 참여자 목록:\n" + "\n".join(lines))

# 명령어: /status5
async def status5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if emoji_to_track and participant_limit:
        await update.message.reply_text(
            f"✅ 현재 이벤트 상태\n- 감지 이모지: {emoji_to_track}\n- 인원 제한: {participant_limit}\n- 현재 참여자 수: {len(participants)}\n- 이벤트 시작됨: {event_started}"
        )
    else:
        await update.message.reply_text("아직 이모지 또는 인원 제한이 설정되지 않았습니다.")

# 메시지 감지 핸들러
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global participants

    if not event_started or not emoji_to_track or not participant_limit:
        return

    message_text = update.message.text
    user_id = update.effective_user.id

    # 이모지 포함 여부 확인
    if emoji_to_track not in message_text:
        return

    # 이미 참여한 유저 제외
    if user_id in [p["id"] for p in participants]:
        return

    # 마감 여부 확인
    if len(participants) >= participant_limit:
        await update.message.reply_text("😥 이벤트가 종료되었습니다. 다음 기회를 노려주세요!")
        return

    # 참여 등록
    participants.append({
        "id": user_id,
        "name": update.effective_user.full_name
    })

    current_count = len(participants)
    if current_count == participant_limit:
        await update.message.reply_text(f"{update.effective_user.full_name}님이 마지막 참여자입니다! ({current_count}/{participant_limit})")
    else:
        await update.message.reply_text(f"{update.effective_user.full_name}님이 이벤트에 참여하셨습니다! ({current_count}/{participant_limit})")

# 실행부
if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()

    TOKEN = os.getenv("BOT5_TOKEN")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start5", start5))
    app.add_handler(CommandHandler("setemoji", setemoji))
    app.add_handler(CommandHandler("setlimit", setlimit))
    app.add_handler(CommandHandler("start_event5", start_event))
    app.add_handler(CommandHandler("reset5", reset5))
    app.add_handler(CommandHandler("list5", list5))
    app.add_handler(CommandHandler("status5", status5))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ bot5_emoji_event.py is running...")
    app.run_polling()
