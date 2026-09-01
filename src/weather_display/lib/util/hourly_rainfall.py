"""Past-hour rainfall at the home automatic weather station.

HKO ``hourlyRainfall`` is measured rain in the last 60 minutes, updated
about every 15 minutes. It is not the gridded 2-hour nowcast. Sha Tin
(RF020) is the nearest official station to 馬鞍山 in this dataset.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

import requests

logger = logging.getLogger(__name__)

HOURLY_RAINFALL_URL = (
    "https://data.weather.gov.hk/weatherAPI/opendata/hourlyRainfall.php"
)
HOME_STATION_ID = "RF020"
HOME_STATION_NAME = "沙田"


@dataclass(frozen=True)
class HourlyRainfall:
    station: str
    station_id: str
    mm: float | None
    obs_time: datetime | None

    @property
    def available(self) -> bool:
        return self.mm is not None

    @property
    def is_wet(self) -> bool:
        return self.mm is not None and self.mm > 0


def _parse_mm(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if text.upper() in {"", "N/A", "NA", "-"}:
        return None
    if text.lower() in {"trace", "微量"}:
        return 0.1
    try:
        return max(0.0, float(text))
    except ValueError:
        return None


def parse_hourly_rainfall(
    payload: dict,
    station_id: str = HOME_STATION_ID,
) -> HourlyRainfall:
    obs_time = None
    raw_time = payload.get("obsTime")
    if raw_time:
        obs_time = datetime.fromisoformat(str(raw_time)).replace(tzinfo=None)

    stations = payload.get("hourlyRainfall") or []
    for row in stations:
        if not isinstance(row, dict):
            continue
        if str(row.get("automaticWeatherStationID") or "") != station_id:
            continue
        name = str(row.get("automaticWeatherStation") or HOME_STATION_NAME)
        return HourlyRainfall(
            station=name,
            station_id=station_id,
            mm=_parse_mm(row.get("value")),
            obs_time=obs_time,
        )
    return HourlyRainfall(
        station=HOME_STATION_NAME,
        station_id=station_id,
        mm=None,
        obs_time=obs_time,
    )


def get_home_hourly_rainfall() -> HourlyRainfall:
    """Fetch Sha Tin past-hour rain. Never raises; ``mm`` is None on failure."""
    try:
        response = requests.get(
            HOURLY_RAINFALL_URL, params={"lang": "tc"}, timeout=15
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("hourlyRainfall payload is not an object")
        return parse_hourly_rainfall(payload)
    except (requests.RequestException, ValueError, TypeError, OSError):
        logger.warning("hourly rainfall unavailable", exc_info=True)
        return HourlyRainfall(
            station=HOME_STATION_NAME,
            station_id=HOME_STATION_ID,
            mm=None,
            obs_time=None,
        )
