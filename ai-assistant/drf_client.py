"""
A thin wrapper over httpx for calls to the existing DRF API.
There is no business logic here, just HTTP requests to ready-made endpoints.
"""

import httpx

from config import settings


class DRFClient:
    def __init__(self, client_token: str | None = None):
        headers = {}
        if client_token:
            headers["Authorization"] = f"Bearer {client_token}"

        # Create ONE client for all future requests of this instance
        # httpx will add base_url to each request, so you don't need to write it in the methods.
        self.client = httpx.AsyncClient(
            base_url=settings.drf_base_url,
            headers=headers
        )

    # Add support for the `async with` context manager,
    # so that the client closes gracefully after work
    async def __aenter__(self) -> "DRFClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.client.aclose()

    async def find_available_slots(
            self, master_id: int, service_id: int, date: str
    ) -> dict:
        # Call self.client.get and specify only the relative path (tail)
        response = await self.client.get(
            "api/appointments/available-slots/by-master/",
            params={"master_id": master_id, "service_id": service_id, "date": date},
        )
        response.raise_for_status()
        return response.json()

    async def search_salons(self, city: str | None = None) -> dict:
        params = {"city": city} if city else {}
        response = await self.client.get(
            "api/salons/",
            params=params,
        )
        response.raise_for_status()
        return response.json()

    async def create_appointment(
            self, master_id: int, service_id: int, date: str, time: str
    ) -> dict:
        response = await self.client.post(
            "api/appointments/",
            json={
                "master_id": master_id,
                "service_id": service_id,
                "appointment_date": date,
                "appointment_time": time,
            },
        )
        response.raise_for_status()
        return response.json()
