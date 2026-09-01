"""Half-hourly rainfall nowcast for a single home location.

Fetches the HKO gridded nowcast CSV (https://data.weather.gov.hk/weatherAPI/hko_data/F3/Gridded_rainfall_nowcast.csv),
picks the grid cell nearest to HOME_LAT/HOME_LON, and returns the four
half-hour amounts. The CSV column is rain in that 30-min window, not a
running total (values rise and fall). ``cumulative_mm`` is summed here.

Returns ``None`` only when the network or the CSV is unavailable. An
all-zero forecast is still returned as a valid result - it means "no rain
in the next 2 hours", which is itself useful information.
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional

import requests

# Home coordinates for the Ma On Shan / Sha Tin area.
# 880 m from the nearest 2 km grid node (22.43, 114.221), well within
# the resolution of the nowcast product, so nearest-node lookup is sufficient.
HOME_LAT = 22.424089489665707
HOME_LON = 114.22673028880479

NOWCAST_URL = (
    "https://data.weather.gov.hk/weatherAPI/hko_data/F3/Gridded_rainfall_nowcast.csv"
)

_COL_UPDATED = "Updated Date and Time (in Hong Kong Time)"
_COL_ENDED = "Ending Date and Time (in Hong Kong Time)"
_COL_LAT = "Latitude (degree)"
_COL_LON = "Longitude (degree)"
_COL_RAIN = "Half-hourly Nowcast Accumulated Rainfall (mm)"


@dataclass
class NowcastSlot:
    """A single half-hour forecast slot.

    ``per_slot_mm`` is rain in the 30 min ending at ``ended_at`` (the CSV
    value). ``cumulative_mm`` is the running sum of those windows from the
    nowcast base time.
    """

    ended_at: datetime
    cumulative_mm: float
    per_slot_mm: float


@dataclass
class HomeNowcast:
    """The 4-slot rainfall forecast for the home location."""

    base_at: datetime
    lat: float
    lon: float
    slots: List[NowcastSlot]

    @property
    def total_mm(self) -> float:
        return self.slots[-1].cumulative_mm if self.slots else 0.0

    @property
    def peak_per_slot_mm(self) -> float:
        return max((s.per_slot_mm for s in self.slots), default=0.0)

    @property
    def first_wet_slot(self) -> Optional[NowcastSlot]:
        """First slot with non-zero per-slot rain, or ``None`` if all dry."""
        for s in self.slots:
            if s.per_slot_mm > 0:
                return s
        return None

    @property
    def is_dry(self) -> bool:
        return self.first_wet_slot is None


def _parse_hkt(value: str) -> datetime:
    return datetime.strptime(value, "%Y%m%d%H%M")


def _load_csv() -> list[dict]:
    """Download and parse the HKO gridded nowcast CSV into row dicts."""
    response = requests.get(NOWCAST_URL, timeout=15)
    response.raise_for_status()
    text = response.content.decode("utf-8-sig")
    rows: list[dict] = []
    for raw in csv.DictReader(io.StringIO(text)):
        rows.append(
            {
                "updatedAt": _parse_hkt(raw[_COL_UPDATED]),
                "endedAt": _parse_hkt(raw[_COL_ENDED]),
                "lat": float(raw[_COL_LAT]),
                "lon": float(raw[_COL_LON]),
                "rainfall": float(raw[_COL_RAIN]),
            }
        )
    return rows


def _pick_nearest(
    nodes: Iterable[tuple[float, float]], lat: float, lon: float
) -> tuple[float, float]:
    """Return the (lat, lon) node with the smallest squared degree distance."""
    nodes = list(nodes)
    if not nodes:
        raise ValueError("nowcast CSV has no grid nodes")
    return min(nodes, key=lambda node: (node[0] - lat) ** 2 + (node[1] - lon) ** 2)


def _nearest_node(rows: list[dict], lat: float, lon: float) -> tuple[float, float]:
    """Find the single grid node nearest to (lat, lon).

    The HKO file is a 121x121 grid (~0.018 deg) with four half-hour slots.
    Unique (lat, lon) pairs are used so lookup does not depend on whether
    the CSV is grouped by slot or by cell.
    """
    nodes = dict.fromkeys((row["lat"], row["lon"]) for row in rows)
    return _pick_nearest(nodes, lat, lon)


def get_home_nowcast() -> Optional[HomeNowcast]:
    """Fetch the 4-slot nowcast for the home location.

    Returns ``None`` if the CSV cannot be retrieved or parsed. An all-zero
    forecast is a valid result (a dry window), not a failure.
    """
    try:
        rows = _load_csv()
        if not rows:
            return None
        node_lat, node_lon = _nearest_node(rows, HOME_LAT, HOME_LON)
        cell = [
            row for row in rows if row["lat"] == node_lat and row["lon"] == node_lon
        ]
        cell.sort(key=lambda row: row["endedAt"])
        if not cell:
            return None

        slots: List[NowcastSlot] = []
        running = 0.0
        for row in cell:
            # Column name says "accumulated" but it is rain in that half
            # hour. Differencing a non-monotonic series invents negatives.
            per_slot = max(0.0, float(row["rainfall"]))
            running = round(running + per_slot, 3)
            slots.append(
                NowcastSlot(
                    ended_at=row["endedAt"],
                    cumulative_mm=running,
                    per_slot_mm=per_slot,
                )
            )

        return HomeNowcast(
            base_at=cell[0]["updatedAt"],
            lat=node_lat,
            lon=node_lon,
            slots=slots,
        )
    except (requests.RequestException, ValueError, KeyError, OSError):
        return None
