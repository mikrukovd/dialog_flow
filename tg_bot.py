import functools
import logging
import os

from telegram import Bot, Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)

from dialogflow import detect_intent_text

logger = logging.getLogger(__name__)


class TelegramLogHandler(logging.Handler):
    def __init__(self, bot: Bot, chat_id: str):
        super().__init__()
        self.bot = bot
        self.chat_id = chat_id

    def emit(self, record):
        message = self.format(record)
        self.bot.send_message(chat_id=self.chat_id, text=message[:4096])


def setup_telegram_logging(tg_bot_token: str, admin_chat_id: str) -> None:
    """Загрузка логгера для отправки в тг"""
    if not (tg_bot_token and admin_chat_id):
        logger.info("Telegram-логирование отключено")
        return

    telegram_bot = Bot(tg_bot_token)

    telegram_handler = TelegramLogHandler(
        telegram_bot,
        admin_chat_id,
    )
    telegram_handler.setLevel(logging.ERROR)
    telegram_handler.setFormatter(
        logging.Formatter("%(asctime)s\n%(levelname)s\n%(message)s")
    )

    logger.addHandler(telegram_handler)


def start(update: Update, context: CallbackContext) -> None:
    """Запуск бота командой /start"""
    logger.info("Бот запущен")
    update.message.reply_text("Бот запущен")


def dialog(project_id: str, update: Update, context: CallbackContext) -> None:
    """Обрабатывает текстовое сообщение и отвечает через DialogFlow"""
    user_id = update.effective_user.id
    user_text = update.message.text

    logger.info(f"Получено сообщение от пользователя {user_id}: {user_text}")
    try:
        result = detect_intent_text(
            project_id=project_id,
            session_id=str(user_id),
            text=update.message.text,
            language_code="ru",
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

    except Exception as error:
        logger.exception(f"Ошибка при обработке сообщения от {user_id}: {error}")
        update.message.reply_text("Произошла ошибка при обработке сообщения")


def main():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    project_id = os.getenv("PROJECT_ID")
    tg_bot_token = os.getnev("TG_BOT_TOKEN")
    admin_chat_id = os.getenv("ADMIN_CHAT_ID")

    setup_telegram_logging(tg_bot_token, admin_chat_id)

    updater = Updater(tg_bot_token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(
        MessageHandler(
            Filters.text & ~Filters.command, functools.partial(dialog, project_id)
        )
    )

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
