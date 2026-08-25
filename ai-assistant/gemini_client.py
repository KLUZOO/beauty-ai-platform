import google.generativeai as genai

from config import settings

from tools import (
    ASSISTANT_TOOLS,
    dispatch_tool_call
)

from serialization_utils import to_plain


genai.configure(api_key=settings.gemini_api_key)


SYSTEM_INSTRUCTION = """
Ти — дружній AI-асистент beauty-платформи. Твоя єдина зона відповідальності:
- підібрати салон і майстра
- підібрати послугу під потреби клієнта
- знайти вільний час для запису
- забронювати запис (тільки після явного підтвердження клієнта)
- дати загальну пораду по догляду за собою (шкіра, волосся тощо)

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

model = genai.GenerativeModel(
    model_name="gemini-3.6-flash",
    system_instruction=SYSTEM_INSTRUCTION,
    tools=[ASSISTANT_TOOLS],
)


# noinspection PyTypeChecker,PyArgumentList
async def run_conversation(message: str, history: list[dict], client_token: str | None) -> dict:
    """Starts one 'turn' of the conversation asynchronously.

    Takes history as a list[dict] from FastAPI and returns a list[dict].
    """
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
    # The message is already being sent ASYNCHRONOUSLY via await
    response = await chat.send_message_async(message)

    # Asynchronous tool call verification through the first part of the first candidate
    while response.candidates and response.candidates[0].content.parts and response.candidates[0].content.parts[0].function_call:
        # noinspection PyTypeChecker
        function_call = response.candidates[0].content.parts[0].function_call

        tool_result = await dispatch_tool_call(
            name=function_call.name,
            args=dict(function_call.args),
            client_token=client_token,
        )

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
            )
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
