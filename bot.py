import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

# 🔐 Token from Render Environment Variable
TOKEN = os.getenv("BOT_TOKEN")

# ------------------ BOT HANDLERS ------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛒 Buying something", callback_data="buy")]
    ]
    await update.message.reply_text(
        "👋 Hi! I help you think before you decide.\n\nTap an option below 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "buy":
        keyboard = [
            [
                InlineKeyboardButton("🔁 Replacement", callback_data="intent_replacement"),
                InlineKeyboardButton("✨ Upgrade", callback_data="intent_upgrade"),
            ],
            [
                InlineKeyboardButton("😶 Impulse / Desire", callback_data="intent_impulse")
            ],
        ]
        await query.edit_message_text(
            "What kind of purchase is this?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data.startswith("intent_"):
        intent = query.data.split("_", 1)[1]
        context.user_data["intent"] = intent
        await query.edit_message_text("💰 Enter approximate amount (numbers only):")

async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "intent" not in context.user_data:
        return

    try:
        amount = int(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ Please enter numbers only.")
        return

    intent = context.user_data["intent"]

    if amount > 50000:
        cost = "High"
    elif amount > 20000:
        cost = "Medium"
    else:
        cost = "Low"

    if cost == "High" and intent == "upgrade":
        verdict = "⚠️ Wait"
        advice = "High-cost upgrade with low urgency. Waiting 7 days is wise."
    elif cost == "High" and intent == "replacement":
        verdict = "🟡 Careful"
        advice = "Necessary but expensive. Compare options."
    elif cost == "Medium" and intent == "impulse":
        verdict = "⚠️ Pause"
        advice = "Impulse purchases at this level are often regretted."
    else:
        verdict = "🟢 Reasonable"
        advice = "This decision looks manageable."

    reply = (
        "📊 Decision Insight\n"
        "------------------\n"
        f"Intent : {intent.capitalize()}\n"
        f"Amount : ₹{amount}\n"
        f"Cost   : {cost}\n\n"
        f"Verdict: {verdict}\n"
        f"Advice : {advice}"
    )

    await update.message.reply_text(reply)
    context.user_data.clear()

# ------------------ RENDER PORT KEEP-ALIVE ------------------

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

# ------------------ MAIN ------------------

def main():
    if not TOKEN:
        raise ValueError("❌ BOT_TOKEN environment variable not set")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount))

    # Start HTTP server for Render
    threading.Thread(target=run_server, daemon=True).start()

    print("🤖 Insight Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
