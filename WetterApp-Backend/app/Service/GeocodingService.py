import os
from dataclasses import dataclass
from functools import lru_cache

import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
# Nominatim verlangt einen aussagekräftigen User-Agent, siehe Usage Policy.
USER_AGENT = os.getenv("GEOCODER_USER_AGENT", "WetterApp/1.0")
TIMEOUT_SECONDS = 10


class GeocodingError(Exception):
    """Der Geocoding-Dienst ist nicht erreichbar oder antwortet fehlerhaft."""


@dataclass(frozen=True)
class GeoLocation:
    latitude: float
    longitude: float
    display_name: str | None


# Cache schont das Rate-Limit von Nominatim (max. 1 Anfrage pro Sekunde).
@lru_cache(maxsize=256)
def geocode(address: str) -> GeoLocation:
    """Wandelt eine Adresse in Deutschland in Koordinaten um.

    Raises:
        ValueError: Wenn die Adresse nicht gefunden wird.
        GeocodingError: Wenn der Dienst nicht erreichbar ist.
    """
    try:
        response = requests.get(
            NOMINATIM_URL,
            params={"q": address, "format": "jsonv2", "countrycodes": "de", "limit": 1},
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        results = response.json()
    except requests.RequestException as exc:
        raise GeocodingError(f"Geocoding fehlgeschlagen: {exc}") from exc

    if not results:
        raise ValueError(f"Adresse nicht gefunden: {address!r}")

    best = results[0]
    return GeoLocation(
        latitude=float(best["lat"]),
        longitude=float(best["lon"]),
        display_name=best.get("display_name"),
    )
