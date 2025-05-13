import os
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, filters
import nest_asyncio

nest_asyncio.apply()

TOKEN = os.getenv("BOT3_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
SETTINGS_PATH = "bot3_rule.json"

config = {
    "rule_message": "📌 기본 룰입니다. /setrule3으로 변경할 수 있습니다."
}

def load_settings():
    if os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, "r") as f:
            config.update(json.load(f))

def save_settings():
    with open(SETTINGS_PATH, "w") as f:
        json.dump(config, f)

# 명령어: /rule3
async def show_rule3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(config["rule_message"])

# 명령어: /setrule3
async def set_rule3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        await update.effective_message.reply_text("⛔ 관리자만 룰을 설정할 수 있습니다.")
        return
    new_rule = " ".join(context.args)
    if not new_rule:
        await update.effective_message.reply_text("❗ 설정할 룰 메시지를 입력해주세요.")
        return
    config["rule_message"] = new_rule
    save_settings()
    await update.effective_message.reply_text("✅ 룰 메시지가 설정되었습니다.")

# 실행부
async def main():
    load_settings()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("rule3", show_rule3, filters=filters.ALL))
    app.add_handler(CommandHandler("setrule3", set_rule3, filters=filters.ALL))

    print("✅ bot3_rule_forwarder is running...")
    await app.run_polling()

def safe_main():
    import asyncio
    asyncio.run(main())

if __name__ == "__main__":
    safe_main()
