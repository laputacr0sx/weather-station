"""Indoor temperature and humidity from Home Assistant.

The dashboard reads six Aqara temp/humidity pairs. Credentials stay in the
environment (or a gitignored ``.env``): ``HA_URL`` and ``HA_TOKEN``. The token
is a long-lived Home Assistant access token and is never written into source.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import requests

HA_URL_ENV = "HA_URL"
HA_TOKEN_ENV = "HA_TOKEN"
DEFAULT_HA_URL = "http://192.168.1.54:8123"

# Entity order is the card order. Names are Chinese because the panel is read
# by children and older people; Home Assistant's English device names are not
# shown.
ROOM_SPECS = (
    (
        "sensor.aqara_temp_humidity_sensor_temperature",
        "sensor.aqara_temp_humidity_sensor_humidity",
        "客房",
    ),
    (
        "sensor.aqara_temp_humidity_sensor_temperature_2",
        "sensor.aqara_temp_humidity_sensor_humidity_2",
        "睡房門口",
    ),
    (
        "sensor.aqara_temp_humidity_sensor_temperature_3",
        "sensor.aqara_temp_humidity_sensor_humidity_3",
        "睡房",
    ),
    (
        "sensor.aqara_temp_humidity_sensor_temperature_4",
        "sensor.aqara_temp_humidity_sensor_humidity_4",
        "客廳",
    ),
    (
        "sensor.aqara_temp_humidity_sensor_temperature_5",
        "sensor.aqara_temp_humidity_sensor_humidity_5",
        "大門",
    ),
    (
        "sensor.aqara_temp_humidity_sensor_temperature_6",
        "sensor.aqara_temp_humidity_sensor_humidity_6",
        "露台",
    ),
)

_MISSING = {"", "unknown", "unavailable", "none", "null"}


class HomeAssistantError(RuntimeError):
    """Home Assistant could not be read. The message never includes the token."""


@dataclass(frozen=True)
class RoomClimate:
    name: str
    temperature_c: float | None
    humidity_pct: float | None


def _number(state: object) -> float | None:
    if state is None:
        return None
    text = str(state).strip()
    if text.lower() in _MISSING:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def rooms_from_states(states: dict) -> list[RoomClimate]:
    """Pair temperature and humidity entities into six room cards."""
    rooms: list[RoomClimate] = []
    for temp_id, humidity_id, name in ROOM_SPECS:
        temp = states.get(temp_id) or {}
        humidity = states.get(humidity_id) or {}
        rooms.append(
            RoomClimate(
                name=name,
                temperature_c=_number(temp.get("state")),
                humidity_pct=_number(humidity.get("state")),
            )
        )
    return rooms


def placeholder_rooms() -> list[RoomClimate]:
    return [
        RoomClimate(name=fallback, temperature_c=None, humidity_pct=None)
        for _temp_id, _humidity_id, fallback in ROOM_SPECS
    ]


def load_dotenv(path: Path | None = None) -> None:
    """Fill missing environment variables from a ``.env`` file.

    Existing variables win, so a shell export is not overwritten. Values are
    not logged.
    """
    env_path = path or _default_env_path()
    try:
        text = env_path.read_text(encoding="utf-8")
    except OSError:
        return
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        os.environ[key] = value.strip().strip("'").strip('"')


def fetch_states(url: str, token: str, timeout: float = 20) -> dict:
    """GET ``/api/states`` and keep only the room entities."""
    wanted = {entity_id for spec in ROOM_SPECS for entity_id in spec[:2]}
    try:
        response = requests.get(
            url.rstrip("/") + "/api/states",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        raise HomeAssistantError(f"Home Assistant request failed: {exc.__class__.__name__}") from exc
    except ValueError as exc:
        raise HomeAssistantError("Home Assistant returned a body that is not JSON") from exc
    if not isinstance(payload, list):
        raise HomeAssistantError("Home Assistant /api/states was not a list")
    return {
        item.get("entity_id"): item
        for item in payload
        if isinstance(item, dict) and item.get("entity_id") in wanted
    }


def fetch_rooms() -> list[RoomClimate]:
    """Read the six rooms using ``HA_URL`` and ``HA_TOKEN``."""
    load_dotenv()
    url = os.environ.get(HA_URL_ENV, DEFAULT_HA_URL).strip() or DEFAULT_HA_URL
    token = os.environ.get(HA_TOKEN_ENV, "").strip()
    if not token:
        raise HomeAssistantError("HA_TOKEN is not set")
    return rooms_from_states(fetch_states(url, token))


def _default_env_path() -> Path:
    # src/weather_display/lib/util/home_assistant.py -> repo root
    return Path(__file__).resolve().parents[4] / ".env"
