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

    async def search_salons(self, city: str | None = None, name: str | None = None) -> dict:
        params = {k: v for k, v in {"city": city, "name": name}.items() if v}

        response = await self.client.get(
            "api/salons/",
            params=params,
        )
        response.raise_for_status()
        data = response.json()

        salons_list = data.get("results", data) if isinstance(data, dict) else data

        cleaned_salons = [
            {
                "id": salon.get("id"),
                "name": salon.get("name"),
                "city": salon.get("location", {}).get("city_name") if isinstance(salon.get("location"), dict) else None,
                "address": salon.get("location", {}).get("address") if isinstance(salon.get("location"),
                                                                                  dict) else None,
                "rating": salon.get("average_rating"),
                "total_reviews": salon.get("total_reviews"),
            }
            for salon in salons_list
        ]

        return {"salons": cleaned_salons}
