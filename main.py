
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, filters, ContextTypes
)
import smtplib
from email.mime.text import MIMEText
import os

# --- Bot Config ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# --- Logging ---
logging.basicConfig(level=logging.INFO)

# --- Conversation States ---
NAME, ADDRESS, ORDER = range(3)

# --- Email Sender ---
def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_ADDRESS

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, EMAIL_ADDRESS, msg.as_string())

# --- Bot Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data["telegram_username"] = f"@{user.username}" if user.username else "No username"
    context.user_data["telegram_user_id"] = user.id
    await update.message.reply_text("Welcome to Couture Cartel! Let’s start your order.\n\nWhat’s your full name?")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Thanks! Now what’s your delivery address?")
    return ADDRESS

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["address"] = update.message.text
    await update.message.reply_text("Almost done! What would you like to order?")
    return ORDER

async def get_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order"] = update.message.text

    summary = (
        f"**NEW ORDER**\n\n"
        f"Name: {context.user_data['name']}\n"
        f"Address: {context.user_data['address']}\n"
        f"Order: {context.user_data['order']}\n\n"
        f"Telegram Username: {context.user_data['telegram_username']}\n"
        f"Telegram ID: {context.user_data['telegram_user_id']}"
    )

    # Send to Admin Telegram
    await context.bot.send_message(chat_id=ADMIN_ID, text=summary)

    # Send Email
    send_email("New Couture Cartel Order", summary)

    await update.message.reply_text("Thanks! Your order has been received. We’ll be in touch soon.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Order cancelled. You can start again anytime with /start.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            ORDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_order)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
