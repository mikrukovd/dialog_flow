import logging
import os

from google.api_core.exceptions import GoogleAPICallError
from google.cloud import dialogflow
from telegram import Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)

PROJECT_ID = os.getenv("PROJECT_ID")
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
LANGUAGE_CODE = "ru"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


def detect_intent_text(
    project_id: str, session_id: str, text: str, language_code: str
) -> dict:
    """
    Возвращает результат распознавания намерения.
    Использует Google Cloud DialogFlow.
    """
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, session_id)

    text_input = dialogflow.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)

    response = session_client.detect_intent(
        request={"session": session, "query_input": query_input}
    )

    return {
        "intent_name": response.query_result.intent.display_name,
        "confidence": response.query_result.intent_detection_confidence,
        "fulfillment_text": response.query_result.fulfillment_text,
    }


def start(update: Update, context: CallbackContext) -> None:
    """Запуск бота командой /start"""
    logger.info("Бот запущен")
    update.message.reply_text("Бот запущен")


def dialog(update: Update, context: CallbackContext) -> None:
    """Обрабатывает текстовое сообщение и отвечает через DialogFlow"""
    user_name = update.effective_user.name
    user_text = update.message.text

    logger.info(f"Получено сообщение от пользователя {user_name}: {user_text}")
    try:
        result = detect_intent_text(
            project_id=PROJECT_ID,
            session_id=str(update.effective_user.id),
            text=update.message.text,
            language_code=LANGUAGE_CODE,
        )

        update.message.reply_text(
            f"{result['fulfillment_text']}",
        )
        logger.info(f"Ответ пользователю {user_name}: {result['fulfillment_text']}")
    except GoogleAPICallError as error:
        logger.error(f"Ошибка при обработке сообщения от {user_name}: {error}")
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
