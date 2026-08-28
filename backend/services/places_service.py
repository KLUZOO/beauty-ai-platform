import random
from contextlib import contextmanager

import requests

from typing import Any

from django.conf import settings


class PlacesService:
    _NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
    _OVERPASS_SERVERS = (
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.private.coffee/api/interpreter",
    )

    _HEADERS = {
        "User-Agent": "BeautyFinder/1.0 (kluzodota@gmail.com)",
    }

    _OVERPASS_QUERY_TEMPLATE = """
                    [out:json][timeout:15];
                    (
                      nwr["shop"~"^(beauty|hairdresser)$"](around:{radius_m},{lat},{lon});
                      nwr["amenity"~"^(beauty_salon|spa)$"](around:{radius_m},{lat},{lon});
                      nwr["beauty"](around:{radius_m},{lat},{lon});
                    );
                    out center tags;
                    """

    _GEOAPIFY_API_KEY = settings.GEOAPIFY_API_KEY
    _GEOAPIFY_PLACES_URL = "https://api.geoapify.com/v2/places"

    _PLACE_CATEGORIES = ",".join([
        "service.beauty",
        "service.beauty.hairdresser",
        "service.beauty.massage",
        "service.beauty.spa",
        "service.beauty.tanning_salon",
        "leisure.spa",
    ])

    @contextmanager
    def _get_session(
            self,
            out_session: requests.Session | None = None,
    ):
        if out_session is not None:
            out_session.headers.update(self._HEADERS)
            yield out_session
        elif self._session is None:
            with requests.Session() as session:
                session.headers.update(self._HEADERS)
                yield session
        else:
            self._session.headers.update(self._HEADERS)
            yield self._session

    def __init__(
            self,
            address: str,
            radius_m: int = 500,
            session: requests.Session | None = None,
    ):
        self.address = address
        self.radius_m = radius_m
        self._session = session

    @property
    def radius_m(self) -> int:
        return self._radius_m

    @radius_m.setter
    def radius_m(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError("radius_m must be int")
        if value >= 0:
            self._radius_m = value
        else:
            raise ValueError("radius_m must be >= 0")

    def get_coordinates(
            self,
            session: requests.Session | None = None,
            address: str | None = None,
    ) -> tuple[float, float]:
        if address is None:
            address = self.address
        with self._get_session(session) as session:
            response = session.get(
                self._NOMINATIM_URL,
                params={
                    "q": address,
                    "format": "jsonv2",
                    "limit": 1,
                },
                timeout=10,
            )

            response.raise_for_status()

            data = response.json()

        if not data:
            raise ValueError("Address not found.")

        return float(data[0]["lat"]), float(data[0]["lon"])

    @classmethod
    def _build_query(cls, lat: float, lon: float, radius_m: int) -> str:
        return cls._OVERPASS_QUERY_TEMPLATE.format(radius_m=radius_m, lat=lat, lon=lon)

    @staticmethod
    def _parse_element(element: dict[str, Any]) -> dict[str, Any]:
        if "lat" in element:
            latitude, longitude = element["lat"], element["lon"]
        else:
            center = element["center"]
            latitude, longitude = center["lat"], center["lon"]

        tags = element.get("tags", {})

        address = ", ".join(
            filter(
                None,
                (tags.get("addr:street"), tags.get("addr:housenumber"), tags.get("addr:city")),
            )
        )

        return {
            "name": tags.get("name", "Unknown"),
            "shop_type": tags.get("shop"),
            "address": address,
            "lat": latitude,
            "lon": longitude,
        }

    def find_places_overpass(
            self,
            coordinate: tuple[float, float] | None = None,
            radius_m: int | None = None,
            session: requests.Session | None = None,
    ) -> list[dict[str, Any]]:
        if coordinate is None:
            coordinate = self.get_coordinates()
        if radius_m is None:
            radius_m = self.radius_m
        lat, lon = coordinate

        query = self._build_query(lat, lon, radius_m)

        servers = list(self._OVERPASS_SERVERS)
        random.shuffle(servers)

        data: dict[str, Any] | None = None

        last_exception = None
        with self._get_session(session) as session:
            for server in servers:
                try:
                    response = session.post(server, data=query, timeout=15)
                    response.raise_for_status()
                    data = response.json()
                    break
                except requests.RequestException as exc:
                    last_exception = exc
            else:
                raise RuntimeError(
                    "All Overpass servers are unavailable."
                ) from last_exception

        return [self._parse_element(element) for element in data.get("elements", ())]

    def find_places_geoapify(
            self,
            coordinate: tuple[float, float] | None = None,
            radius_m: int | None = None,
            session: requests.Session | None = None,
    ) -> list[dict[str, Any]]:
        if coordinate is None:
            coordinate = self.get_coordinates()
        if radius_m is None:
            radius_m = self.radius_m
        lat, lon = coordinate

        params = {
            "categories": self._PLACE_CATEGORIES,
            "filter": f"circle:{lon},{lat},{radius_m}",
            "bias": f"proximity:{lon},{lat}",
            "limit": 100,
            "apiKey": self._GEOAPIFY_API_KEY,
        }
        with self._get_session(session) as session:
            try:
                response = session.get(self._GEOAPIFY_PLACES_URL, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
            except requests.RequestException as exc:
                raise RuntimeError(
                    "Geoapify request failed."
                ) from exc

        places = []

        for feature in data.get("features", ()):
            props = feature.get("properties", {})
            categories = props.get("categories", [])

            shop_type = next(
                (c.split(".", 1)[1] for c in categories if c.startswith("service.beauty.")),
                None,
            )

            places.append(
                {
                    "name": props.get("name", "Unknown"),
                    "shop_type": shop_type,
                    "address": props.get("formatted", ""),
                    "lat": props.get("lat"),
                    "lon": props.get("lon"),
                }
            )

        return places

    def find_places(
            self,
            radius_m: int | None = None,
    ) -> list[dict[str, Any]] | None:
        if radius_m is None:
            radius_m = self.radius_m
        last_exception = None

        providers = (
            self.find_places_geoapify,
            self.find_places_overpass,
        )

        with self._get_session() as session:
            coordinate = self.get_coordinates(session)
            for provider in providers:
                try:
                    return provider(coordinate, radius_m, session)
                except RuntimeError as exc:
                    last_exception = exc

        raise RuntimeError(
            "No places provider is available."
        ) from last_exception
