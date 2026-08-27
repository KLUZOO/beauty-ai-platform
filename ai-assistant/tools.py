"""
Descriptions of "tools" (function declarations) that Gemini can call,
plus a dispatcher that actually executes the call via DRFClient.
"""

import httpx
from google.generativeai.types import (
    FunctionDeclaration,
    Tool
)

from drf_client import DRFClient

find_available_slots_declaration = FunctionDeclaration(
    name="find_available_slots",
    description=(
        "Знайти вільні часові слоти для запису до конкретного майстра "
        "на конкретну послугу і дату."
    ),
    parameters={
        "type": "object",
        "properties": {
            "master_id": {"type": "integer", "description": "ID майстра"},
            "service_id": {"type": "integer", "description": "ID послуги"},
            "date": {
                "type": "string",
                "description": "Дата у форматі YYYY-MM-DD",
            },
        },
        "required": ["master_id", "service_id", "date"],
    },
)

search_salons_declaration = FunctionDeclaration(
    name="search_salons",
    description="Знайти салони, за бажанням відфільтровані по місту.",
    parameters={
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "Місто (необов'язково)"},
        },
    },
)

create_appointment_declaration = FunctionDeclaration(
    name="create_appointment",
    description=(
        "Забронювати запис до майстра на конкретну послугу, дату і час. "
        "Викликати тільки після того, як клієнт явно підтвердив бронювання."
    ),
    parameters={
        "type": "object",
        "properties": {
            "master_id": {"type": "integer"},
            "service_id": {"type": "integer"},
            "date": {"type": "string", "description": "YYYY-MM-DD"},
            "time": {"type": "string", "description": "HH:MM"},
        },
        "required": ["master_id", "service_id", "date", "time"],
    },
)

ASSISTANT_TOOLS = Tool(
    function_declarations=[
        find_available_slots_declaration,
        search_salons_declaration,
        create_appointment_declaration,
    ]
)


async def dispatch_tool_call(name: str, args: dict, client_token: str | None) -> dict:
    """Makes the actual call to DRF according to the tool name chosen by Gemini.

    Has built-in error handling in case the Django backend is unavailable.
    """
    try:
        async with DRFClient(client_token=client_token) as drf:

            if name == "find_available_slots":
                return await drf.find_available_slots(**args)

            if name == "search_salons":
                return await drf.search_salons(**args)

            if name == "create_appointment":
                return await drf.create_appointment(**args)

            return {"error": f"Unknown tool: {name}"}

    except httpx.HTTPStatusError as e:
        # If DRF returned 404, 400 or 422 (no data or incorrect parameters)
        if e.response.status_code in (400, 404, 422):
            return {
                "status": "not_found",
                "message": f"Запитувані дані не знайдено в базі (код {e.response.status_code})."
            }
        # If 500, 502, 503 (real backend crash)
        return {
            "error": "система бронювання тимчасово недоступна через технічні проблеми на бекенді",
            "details": str(e)
        }

    except (httpx.ConnectError, httpx.TimeoutException) as e:
        # Network connection errors
        return {
            "error": "не вдалося з'єднатися з сервером бронювання",
            "details": str(e)
        }
    except Exception as e:
        # McCombo for other unexpected errors 👀
        return {
            "error": "невідома помилка під час виконання інструменту",
            "details": str(e)
        }
