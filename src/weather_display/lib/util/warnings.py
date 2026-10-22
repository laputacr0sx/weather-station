"""Active Hong Kong Observatory warnings.

``warnsum`` is the official summary. An empty object means nothing is in
force. The level lives in ``code`` (WRAINA, TC8SE, …), not in the property
name. Cancelled warnings are omitted.
"""
from __future__ import annotations

from dataclasses import dataclass

import requests

from weather_display import HKO_URL

_TONE = {
    "WFIREY": "yellow",
    "WFIRER": "red",
    "WFROST": "blue",
    "WHOT": "red",
    "WCOLD": "blue",
    "WMSGNL": "yellow",
    "WRAINA": "yellow",
    "WRAINR": "red",
    "WRAINB": "black",
    "WFNTSA": "yellow",
    "WL": "red",
    "TC1": "yellow",
    "TC3": "yellow",
    "TC8NE": "red",
    "TC8SE": "red",
    "TC8NW": "red",
    "TC8SW": "red",
    "TC9": "red",
    "TC10": "black",
    "WTMW": "yellow",
    "WTS": "yellow",
}
_RANK = {"yellow": 1, "blue": 1, "red": 2, "black": 3}


@dataclass(frozen=True)
class WeatherWarning:
    name: str
    tone: str


def parse_warnings(payload: dict | None) -> list[WeatherWarning]:
    if not isinstance(payload, dict):
        return []
    found: list[WeatherWarning] = []
    for item in payload.values():
        if not isinstance(item, dict):
            continue
        action = str(item.get("actionCode") or "ISSUE").upper()
        if action == "CANCEL":
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        code = str(item.get("code") or "").upper()
        found.append(WeatherWarning(name=name, tone=_TONE.get(code, "yellow")))
    found.sort(key=lambda warning: _RANK.get(warning.tone, 0), reverse=True)
    return found


def get_warnings() -> list[WeatherWarning] | None:
    """Active warnings, or ``None`` when the summary could not be read.

    An empty list means the Observatory published an empty summary. ``None``
    means the request failed, which is not the same as "no warning".
    """
    try:
        payload = requests.get(
            HKO_URL,
            params={"dataType": "warnsum", "lang": "tc"},
            timeout=15,
        ).json()
    except (requests.RequestException, ValueError):
        return None
    return parse_warnings(payload)
