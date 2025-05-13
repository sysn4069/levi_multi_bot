import os
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, filters
import nest_asyncio

nest_asyncio.apply()

TOKEN = os.getenv("BOT3_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
SETTINGS_PATH = "/data/bot3_rule.json"

config = {
    "rule_message": "\ud83d\udccc \uae30\ubcf8 \ub8e8\ub4le\uc785\ub2c8\ub2e4. /setrule3\ub85c \ubcc0\uacbd\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4."
}

def load_settings():
    if os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, "r") as f:
            config.update(json.load(f))

def save_settings():
    with open(SETTINGS_PATH, "w") as f:
        json.dump(config, f)

async def show_rule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(config["rule_message"])

async def set_rule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        await update.effective_message.reply_text("\u26d4 \uad00\ub9ac\uc790\ub9cc \ub8e8\ub4le\uc744 \uc124\uc815\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4.")
        return
    new_rule = " ".join(context.args)
    if not new_rule:
        await update.effective_message.reply_text("\u2753 \uc124\uc815\ud560 \ub8e8\ub4le \uba54\uc2dc\uc9c0\ub97c \uc785\ub825\ud574\uc8fc\uc138\uc694.")
        return
    config["rule_message"] = new_rule
    save_settings()
    await update.effective_message.reply_text("\u2705 \ub8e8\ub4le \uba54\uc2dc\uc9c0\uac00 \uc124\uc815\ub418\uc5c8\uc2b5\ub2c8\ub2e4.")

async def main():
    load_settings()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("rule3", show_rule, filters=filters.ALL))
    app.add_handler(CommandHandler("setrule3", set_rule, filters=filters.ALL))

    await app.run_polling()

def safe_main():
    import asyncio
    asyncio.run(main())

if __name__ == "__main__":
    safe_main()
