import json
import logging
import os

from google.cloud import dialogflow

PROJECT_ID = os.getenv("PROJECT_ID")

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
        "fallback": response.query_result.intent.is_fallback,
    }


def create_intent_from_json(intents_file_path: str) -> None:
    """
    Создаёт Intent на основе JSON-файла.

    Пример структуры JSON:
    {
        "Как устроиться к вам на работу": {
            "questions": [],
            "answer":
        }
    }
    """
    with open(intents_file_path, "r", encoding="utf-8") as file:
        intents_data = json.load(file)

    dialogflow_client = dialogflow.IntentsClient()

    agent_resource_path = f"projects/{PROJECT_ID}/locations/global/agent"

    for intent_display_name, intent_details in intents_data.items():
        # Обучающие фразы
        training_phrase_objects = []
        for question_text in intent_details.get("questions", []):
            training_phrase_part = dialogflow.Intent.TrainingPhrase.Part(
                text=question_text
            )
            training_phrase_object = dialogflow.Intent.TrainingPhrase(
                parts=[training_phrase_part]
            )
            training_phrase_objects.append(training_phrase_object)

        # Ответ
        answer_text = intent_details["answer"]
        reply_message = dialogflow.Intent.Message(
            text=dialogflow.Intent.Message.Text(text=[answer_text])
        )

        intent_to_create = dialogflow.Intent(
            display_name=intent_display_name,
            training_phrases=training_phrase_objects,
            messages=[reply_message],
        )

        try:
            created_intent = dialogflow_client.create_intent(
                request={"parent": agent_resource_path, "intent": intent_to_create}
            )
            logger.info(
                f"Создан intent {created_intent.display_name} (ID: {created_intent.name})"
            )
        except Exception as error:
            logger.error(f"Ошибка создания intent {intent_display_name}: {error}")


if __name__ == "__main__":
    create_intent_from_json("intents_data.json")
