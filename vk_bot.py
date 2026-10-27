import logging
import os
import random

import vk_api as vk
from telegram import Bot
from vk_api.longpoll import VkEventType, VkLongPoll

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


def handle_message(event, vk_api, project_id: str) -> None:
    """Обрабатывает текстовое сообщение и отвечает через DialogFlow"""
    user_id = event.user_id
    user_text = event.text

    logger.info(f"Получено сообщение от пользователя {user_id}: {user_text}")
    try:
        result = detect_intent_text(
            project_id=project_id,
            session_id=f"vk-{user_id}",
            text=user_text,
            language_code="ru",
        )
        logger.info(
            f"Интент {result['intent_name']} уверенность {result['confidence']}"
        )

        if result["fallback"]:
            logger.info(f"Неизвестный запрос от пользователя {user_id}")
        else:
            vk_api.messages.send(
                user_id=user_id,
                message=f"{result['fulfillment_text']}",
                random_id=random.randint(1, 1000),
            )
            logger.info(f"Ответ пользователю {user_id}: {result['fulfillment_text']}")
    except Exception as error:
        logger.exception(f"Ошибка при обработке сообщения от {user_id}: {error}")


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    project_id = os.getenv("PROJECT_ID")
    vk_group_token = os.getenv("VK_GROUP_TOKEN")
    admin_chat_id = os.getenv("ADMIN_CHAT_ID")
    tg_bot_token = os.getenv("TG_BOT_TOKEN")

    setup_telegram_logging(tg_bot_token, admin_chat_id)

    vk_session = vk.VkApi(token=vk_group_token)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            handle_message(event, vk_api, project_id)
