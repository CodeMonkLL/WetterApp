import os
from dataclasses import dataclass
from functools import lru_cache

import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"
# Zoom 13 liefert Dörfer und Ortsteile, keine einzelnen Straßen oder Häuser.
REVERSE_ZOOM = 13
# 3 Nachkommastellen (~100 m) fassen nahe Klicks im Cache zusammen.
REVERSE_CACHE_DECIMALS = 3
# Vom kleinsten zum größten Ort, der erste vorhandene gilt als nächster Ort.
LOCALITY_KEYS = ("hamlet", "village", "town", "city", "municipality")
REGION_KEYS = ("county", "state")
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


def reverse_geocode(latitude: float, longitude: float) -> str | None:
    """Liefert den Namen des nächsten Ortes, z.B. "Mühlhausen, Unstrut-Hainich-Kreis".

    Returns:
        None, wenn an der Stelle kein Ort bekannt ist, z.B. auf dem Meer.

    Raises:
        GeocodingError: Wenn der Dienst nicht erreichbar ist.
    """
    return _reverse_geocode(
        round(latitude, REVERSE_CACHE_DECIMALS),
        round(longitude, REVERSE_CACHE_DECIMALS),
    )


@lru_cache(maxsize=256)
def _reverse_geocode(latitude: float, longitude: float) -> str | None:
    try:
        response = requests.get(
            NOMINATIM_REVERSE_URL,
            params={
                "lat": latitude,
                "lon": longitude,
                "format": "jsonv2",
                "zoom": REVERSE_ZOOM,
                "accept-language": "de",
            },
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        result = response.json()
    except requests.RequestException as exc:
        raise GeocodingError(f"Geocoding fehlgeschlagen: {exc}") from exc

    # Ohne Treffer antwortet Nominatim mit 200 und {"error": "Unable to geocode"}.
    if not result or "error" in result:
        return None
    return _place_name(result)


def _place_name(result: dict) -> str | None:
    address = result.get("address") or {}
    locality = next((address[k] for k in LOCALITY_KEYS if address.get(k)), None)
    if not locality:
        return result.get("display_name")
    region = next((address[k] for k in REGION_KEYS if address.get(k) and address[k] != locality), None)
    return f"{locality}, {region}" if region else locality
