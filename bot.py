import os
import logging
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# === 🔐 Настройки ===
TOKEN = os.getenv("TELEGRAM_TOKEN") or "УКАЖИ_ТОКЕН_ТУТ_ЕСЛИ_ТЕСТИРУЕШЬ_ЛОКАЛЬНО"
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# === 🧠 Настройка логов ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === 🧭 Команды ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Пользователь запустил /start")
    keyboard = [
        ["📰 Советы", "💻 IT для чайников"],
        ["📖 История Лазурного", "ℹ️ О сайте"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "👋 Привет! Я VibegBot — помощник сайта vibegnews.tilda.ws.\n"
        "Выбери раздел или задай вопрос.",
        reply_markup=reply_markup
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌐 <b>О проекте:</b>\n"
        "Сайт <a href='https://vibegnews.tilda.ws'>VibegNews</a> — это полезные советы по дому, технике и жизни.\n"
        "Задай вопрос — я помогу найти нужную статью!",
        parse_mode="HTML"
    )

async def site_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 Полезные материалы:\n"
        "🏠 <a href='https://vibegnews.tilda.ws/#rec849880788'>Советы по домоводству</a>\n"
        "💻 <a href='https://vibegnews.tilda.ws/#rec849898378'>Советы IT для «чайников»</a>\n"
        "🏖️ <a href='https://drive.google.com/file/d/1fSXGoHw7V9sPPg1VLBjzLua4nTqvHSI3/view'>История посёлка Лазурное</a>",
        parse_mode="HTML"
    )

# === 🧠 Интеграция с Mistral AI ===
def ask_mistral(question: str) -> str:
    if not MISTRAL_API_KEY:
        return "⚙️ Mistral API не настроен. Укажи ключ в переменной MISTRAL_API_KEY."

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mistral-small-latest",
        "messages": [
            {
                "role": "system",
                "content": "Ты помощник сайта vibegnews.tilda.ws. Отвечай кратко, дружелюбно. При необходимости вставляй ссылки на статьи с vibegnews.tilda.ws."
            },
            {"role": "user", "content": question}
        ]
    }

    try:
        resp = requests.post("https://api.mistral.ai/v1/chat/completions", headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Ошибка Mistral: {e}")
        return "⚠️ Не удалось получить ответ от Mistral AI."

# === 📨 Ответы на сообщения ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    logger.info(f"Сообщение: {text}")

    if "совет" in text:
        await site_links(update, context)
    elif "лазурн" in text:
        await update.message.reply_text(
            "🏖️ Вот история посёлка Лазурное:\n"
            "👉 <a href='https://drive.google.com/file/d/1fSXGoHw7V9sPPg1VLBjzLua4nTqvHSI3/view'>Читать</a>",
            parse_mode="HTML"
        )
    elif "сайт" in text or "о проекте" in text:
        await about(update, context)
    else:
        answer = ask_mistral(text)
        await update.message.reply_text(answer, parse_mode="HTML")

# === ⚠️ Обработка ошибок ===
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Ошибка: {context.error}")
    if update and update.message:
        await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")

# === 🚀 Основная функция ===
def main():
    logger.info("Запуск VibegBot...")
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    app.run_polling(allowed_updates=Update.ALL_TYPES)
    logger.info("VibegBot запущен!")

if __name__ == "__main__":
    main()
