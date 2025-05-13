import os
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, filters
import nest_asyncio

nest_asyncio.apply()

TOKEN = os.getenv("BOT3_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
SETTINGS_PATH = "/render/data/bot3_rule.json"

config = {
    "rule_message": "📌 기본 룰입니다. /setrule3로 변경할 수 있습니다."
}

def load_settings():
    if os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, "r") as f:
            config.update(json.load(f))

def save_settings():
    with open(SETTINGS_PATH, "w") as f:
        json.dump(config, f)

async def rule3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(config["rule_message"])

async def setrule3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        return
    new_rule = " ".join(context.args)
    if not new_rule:
        await update.effective_message.reply_text("❗ 설정할 룰 메시지를 입력해주세요.")
        return
    config["rule_message"] = new_rule
    save_settings()
    await update.message.reply_text("✅ 룰 메시지가 설정되었습니다.")

async def main():
    load_settings()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("rule3", rule3, filters=filters.ALL))
    app.add_handler(CommandHandler("setrule3", setrule3, filters=filters.ALL))

    await app.run_polling()

def safe_main():
    import asyncio
    asyncio.run(main())

if __name__ == "__main__":
    safe_main()
