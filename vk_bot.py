import logging
import os
import random

import vk_api as vk
from google.cloud import dialogflow
from vk_api.longpoll import VkEventType, VkLongPoll

PROJECT_ID = os.getenv("PROJECT_ID")
VK_GROUP_TOKEN = os.getenv("VK_GROUP_TOKEN")
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


def dialog(event, vk_api):
    user_id = event.user_id
    user_text = event.text

    logger.info(f"Получено сообщение от пользователя {user_id}: {user_text}")
    try:
        result = detect_intent_text(
            project_id=PROJECT_ID,
            session_id=str(user_id),
            text=user_text,
            language_code=LANGUAGE_CODE,
        )
        vk_api.messages.send(
            user_id=user_id,
            message=f"{result['fulfillment_text']}",
            random_id=random.randint(1, 1000),
        )
        logger.info(f"Ответ пользователю {user_id}: {result['fulfillment_text']}")
    except Exception as error:
        logger.error(f"Ошибка при обработке сообщения от {user_id}: {error}")


if __name__ == "__main__":
    vk_session = vk.VkApi(token=VK_GROUP_TOKEN)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            dialog(event, vk_api)
