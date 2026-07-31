import logging
import os

from google.api_core.exceptions import GoogleAPICallError
from telegram import Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)

from dialogflow import detect_intent_text

PROJECT_ID = os.getenv("PROJECT_ID")
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
LANGUAGE_CODE = "ru"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext) -> None:
    """Запуск бота командой /start"""
    logger.info("Бот запущен")
    update.message.reply_text("Бот запущен")


def dialog(update: Update, context: CallbackContext) -> None:
    """Обрабатывает текстовое сообщение и отвечает через DialogFlow"""
    user_id = update.effective_user.id
    user_text = update.message.text

    logger.info(f"Получено сообщение от пользователя {user_id}: {user_text}")
    try:
        result = detect_intent_text(
            project_id=PROJECT_ID,
            session_id=str(user_id),
            text=update.message.text,
            language_code=LANGUAGE_CODE,
        )
        logger.info(
            f"Интент {result['intent_name']} уверенность {result['confidence']}"
        )

        if result["fallback"]:
            logger.info(f"Неизвестный запрос от пользователя {user_id}")
        else:
            update.message.reply_text(
                f"{result['fulfillment_text']}",
            )
            logger.info(f"Ответ пользователю {user_id}: {result['fulfillment_text']}")

    except GoogleAPICallError as error:
        logger.error(f"Ошибка при обработке сообщения от {user_id}: {error}")
        update.message.reply_text("Произошла ошибка при обработке сообщения")


def main():
    bot_token = TG_BOT_TOKEN
    updater = Updater(bot_token)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, dialog))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
