import google.generativeai as genai
from datetime import datetime
from google.api_core.exceptions import (
    GoogleAPICallError,
    DeadlineExceeded,
    ResourceExhausted
)

from fastapi import HTTPException

from config import settings

from tools import (
    ASSISTANT_TOOLS,
    dispatch_tool_call
)

from serialization_utils import to_plain


genai.configure(api_key=settings.gemini_api_key)


def get_system_instruction() -> str:
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_weekday = now.strftime("%A")

    return f"""
Ти — дружній AI-асистент beauty-платформи. Твоя єдина зона відповідальності:
- підібрати салон і майстра
- підібрати послугу під потреби клієнта
- знайти вільний час для запису
- забронювати запис (тільки після явного підтвердження клієнта)
- дати загальну пораду по догляду за собою (шкіра, волосся тощо)

КОНТЕКСТ ЧАСУ ТА ДАТИ:
- Сьогоднішня дата: {current_date} ({current_weekday}).
- Для будь-яких відносних дат ("сьогодні", "завтра", "післязавтра", "наступного вівторка", "цими вихідними") 
  ти ПОВИННА САМОСТІЙНО обчислити точну дату у форматі YYYY-MM-DD, виходячи з {current_date}.
- НЕ запитуй у користувача точне число та місяць, якщо він дав відносну дату (наприклад, "завтра" або "післязавтра") 
  чи вказав розмитий час ("вдень", "зранку", "ввечері"). Одразу шукай вільні слоти на цей період!

ОБРОБКА ОДРУКІВОК ТА НЕЧІТКИХ ЗАПИТІВ:
- Якщо запит користувача містить описки або сленг (наприклад, "хтовільний" = "будь-який вільний майстер", 
  "нарощєня" = "нарощування"), завжди інтерпретуй його за загальним змістом.
- Якщо за результатами пошуку чи виклику інструменту повернулося "status": "not_found" або порожній список, 
  НЕ видавай порожню відповідь. Замість цього дружньо повідом про відсутність конкретного майстра/слоту 
  та запропонуй усі доступні альтернативи (або запитай уточнення).
  
ПРАВИЛА ОБРОБКИ ОПИСОК ТА ВІДСУТНІХ ДАНИХ:
- Якщо в назві міста є явна описка (наприклад, "Кинві", "Кимв", "Лвів"), ВСЕОДНО передавай у пошуковий 
  інструмент нормалізоване місто (наприклад, city="Київ").
- Якщо інструмент пошуку повертає порожній список (салонів/слотів не знайдено), НІКОЛИ не повертай порожню відповідь. 
  Чітко повідом клієнту, що за даними параметрами нічого не знайдено, та запропонуй уточнити місто чи назву.

Завжди спілкуйся українською, коротко і дружньо.
Ніколи не бронюй запис без явного "так, підтверджую" від клієнта.

МЕЖІ РОЗМОВИ:
Якщо клієнт питає щось, що НЕ стосується запису на beauty-послуги, підбору
салону/майстра чи догляду за собою (наприклад: політика, погода, просто
хоче поговорити на абстрактну тему, просить допомогти з чимось стороннім) —
НЕ підтримуй цю розмову як звичайний чат-бот. Замість цього:
1. Коротко і доброзичливо поясни, що ти консультуєш саме з питань запису
   на beauty-послуги, підбору майстра/салону та базового догляду за собою.
2. Одразу запропонуй повернутись до теми — наприклад, запитай, чи потрібна
   допомога з вибором послуги або пошуком вільного часу для запису.

Не вибачайся довго і не пояснюй розлого — одне коротке речення про межі
твоєї компетенції, і одразу перехід до пропозиції допомогти по темі.
"""


REQUEST_OPTIONS = {"timeout": 60.0}


# noinspection PyTypeChecker,PyArgumentList
async def run_conversation(message: str, history: list[dict], client_token: str | None) -> dict:
    """Starts one 'turn' of the conversation asynchronously.

    Takes history as a list[dict] from FastAPI and returns a list[dict].
    """
    model = genai.GenerativeModel(
        model_name="gemini-3.6-flash",
        system_instruction=get_system_instruction(),
        tools=[ASSISTANT_TOOLS],
    )

    gemini_history = []
    for entry in history:
        parts_list = []
        for p in entry.get("parts", []):
            if isinstance(p, str):
                parts_list.append(genai.protos.Part(text=p))
            elif isinstance(p, dict) and "function_call" in p:
                fc = p["function_call"]
                parts_list.append(genai.protos.Part(
                    function_call={"name": fc["name"], "args": fc["args"]}
                ))
            elif isinstance(p, dict) and "function_response" in p:
                fr = p["function_response"]
                parts_list.append(genai.protos.Part(
                    function_response={"name": fr["name"], "response": fr["response"]}
                ))

        gemini_history.append(
            genai.protos.Content(role=entry.get("role"), parts=parts_list)
        )

    chat = model.start_chat(history=gemini_history)

    try:
        # The message is already being sent ASYNCHRONOUSLY via await
        response = await chat.send_message_async(message, request_options=REQUEST_OPTIONS)

        # Asynchronous tool call verification through the first part of the first candidate
        while (
            response.candidates
            and response.candidates[0].content.parts
            and response.candidates[0].content.parts[0].function_call
        ):
            # noinspection PyTypeChecker
            function_call = response.candidates[0].content.parts[0].function_call

            tool_result = await dispatch_tool_call(
                name=function_call.name,
                args=dict(function_call.args),
                client_token=client_token,
            )

            # Protection against empty DB result (if nothing is found for the query)
            if (
                tool_result is None
                or tool_result in ([], {})
                or (isinstance(tool_result, dict) and "salons" in tool_result and not tool_result["salons"])
            ):
                tool_result = {
                    "status": "not_found",
                    "message": "За вказаним запитом або критерієм нічого не знайдено."
                }

            response = await chat.send_message_async(
                genai.protos.Content(
                    parts=[
                        genai.protos.Part(
                            function_response={
                                "name": function_call.name,
                                "response": {"result": tool_result},
                            }
                        )
                    ]
                ),
                request_options=REQUEST_OPTIONS,
            )

    except ResourceExhausted:
        # Intercept Rate Limit from Google API (429)
        raise HTTPException(
            status_code=429,
            detail="Перевищено ліміт запитів до ШІ. Зачекайте 5-10 секунд і спробуйте знову."
        )
    except DeadlineExceeded:
        raise HTTPException(
            status_code=504,
            detail="Сервіс ШІ тимчасово не відповідає. Спробуйте ще раз."
        )
    except GoogleAPICallError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Помилка при зверненні до Gemini API: {str(e)}"
        )

    clean_history = []
    for entry in chat.history:
        parts_list = []
        for part in entry.parts:
            if hasattr(part, "text") and part.text:
                parts_list.append(part.text)
            elif hasattr(part, "function_call") and part.function_call.name:
                parts_list.append({
                    "function_call": {
                        "name": part.function_call.name,
                        "args": to_plain(part.function_call.args)
                    }
                })
            elif hasattr(part, "function_response") and part.function_response.name:
                parts_list.append({
                    "function_response": {
                        "name": part.function_response.name,
                        "response": to_plain(part.function_response.response)
                    }
                })

        clean_history.append({
            "role": entry.role,
            "parts": parts_list
        })

    return {
        "reply": response.text,
        "history": clean_history,
    }
