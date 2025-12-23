import os
import re
import logging
from typing import Final
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# =====================
# ENV
# =====================
load_dotenv(dotenv_path=Path(__file__).with_name(".env"), override=True)

# =====================
# LOGGING
# =====================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# =====================
# CONFIG
# =====================
TELEGRAM_BOT_TOKEN: Final[str] = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

CHUTES_API_KEY: Final[str] = os.getenv("CHUTES_API_KEY", "").strip()
CHUTES_BASE_URL: Final[str] = os.getenv(
    "CHUTES_BASE_URL", "https://llm.chutes.ai/v1"
).strip()
CHUTES_MODEL: Final[str] = os.getenv("CHUTES_MODEL", "").strip()

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN in environment.")
if not CHUTES_API_KEY:
    raise RuntimeError("Missing CHUTES_API_KEY in environment.")
if not CHUTES_MODEL:
    raise RuntimeError("Missing CHUTES_MODEL in environment.")

client = OpenAI(
    api_key=CHUTES_API_KEY,
    base_url=CHUTES_BASE_URL,
)

# =====================
# CONVERSATION STATES
# =====================
ASK_TOPIC, ASK_AUDIENCE, ASK_TONE = range(3)

PROMPT_SYSTEM = (
    "Ти — копірайтер. Відповідай ТІЛЬКИ готовим рекламним лозунгом українською.\n"
    "Не додавай пояснень, міркувань, службових тегів.\n"
    "Формат: один рядок, 5–12 слів."
)

# =====================
# HELPERS
# =====================
def build_user_prompt(topic: str, audience: str, tone: str) -> str:
    return (
        f"Тематика продукту: {topic}\n"
        f"Цільова аудиторія: {audience}\n"
        f"Тон: {tone}\n"
        "Згенеруй один лозунг."
    )

def clean_slogan(text: str) -> str:
    """
    Прибирає ТІЛЬКИ коректні блоки <think>...</think>.
    Нічого іншого не чіпає.
    """
    if not text:
        return ""
    return re.sub(
        r"<think\b[^>]*>.*?</think>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE
    ).strip()

# =====================
# HANDLERS
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("Вкажи тематику продукту:")
    return ASK_TOPIC

async def got_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["topic"] = (update.message.text or "").strip()
    await update.message.reply_text("Вкажи цільову аудиторію:")
    return ASK_AUDIENCE

async def got_audience(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["audience"] = (update.message.text or "").strip()
    await update.message.reply_text(
        "Вкажи тон (дружній, офіційний, жартівливий тощо):"
    )
    return ASK_TONE

async def got_tone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["tone"] = (update.message.text or "").strip()

    topic = context.user_data.get("topic", "")
    audience = context.user_data.get("audience", "")
    tone = context.user_data.get("tone", "")

    user_prompt = build_user_prompt(topic, audience, tone)

    try:
        resp = client.chat.completions.create(
            model=CHUTES_MODEL,
            messages=[
                {"role": "system", "content": PROMPT_SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.6,
            max_tokens=1000,
        )

        raw = resp.choices[0].message.content or ""
        slogan = clean_slogan(raw)

        if not slogan:
            slogan = "Не вдалося згенерувати лозунг. Спробуй ще раз: /start"

        await update.message.reply_text(slogan)

    except Exception:
        logger.exception("LLM call failed")
        await update.message.reply_text(
            "Помилка при зверненні до моделі. Спробуй пізніше."
        )

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("Скасовано. Почати знову: /start")
    return ConversationHandler.END

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Unhandled error: %s", context.error)

# =====================
# MAIN
# =====================
def main() -> None:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_TOPIC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, got_topic)
            ],
            ASK_AUDIENCE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, got_audience)
            ],
            ASK_TONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, got_tone)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    app.add_error_handler(error_handler)

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    import asyncio
    asyncio.set_event_loop(asyncio.new_event_loop())
    main()
