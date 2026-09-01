"""HKO weather warnings and special tips for the dashboard strip.

``warnsum`` is the source of truth for in-force signals. ``swt`` supplies one
short extra line when it adds something the chips do not already say
(typically a pre-signal such as "考慮發出一號"). ``warningInfo`` bulletins
are not consumed - they do not fit on 800x480.

Multiple warnings pack left-to-right on a single inverted row. Overflow
yields in this order: drop the tip, tighten the gap, hide labels, drop the
lowest-severity chip. Real HKO overlap tops out around six signals, which
still fits with labels.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Callable, Sequence

import requests

from weather_display import HKO_URL

logger = logging.getLogger(__name__)

# Highest first. TC8 variants share a rank; rainstorm subtypes do not.
_SEVERITY = {
    "TC10": 100,
    "TC9": 95,
    "TC8NE": 90,
    "TC8SE": 90,
    "TC8NW": 90,
    "TC8SW": 90,
    "WRAINB": 85,
    "WRAINR": 80,
    "TC3": 75,
    "WRAINA": 70,
    "WL": 65,
    "WTS": 60,
    "WTMW": 55,
    "WMSGNL": 50,
    "TC1": 45,
    "WHOT": 40,
    "WCOLD": 40,
    "WFIRER": 35,
    "WFIREY": 30,
    "WFNTSA": 25,
    "WFROST": 20,
}

_LABEL = {
    "WRAINA": "黃雨",
    "WRAINR": "紅雨",
    "WRAINB": "黑雨",
    "WTS": "雷暴",
    "TC1": "一號",
    "TC3": "三號",
    "TC8NE": "八號",
    "TC8SE": "八號",
    "TC8NW": "八號",
    "TC8SW": "八號",
    "TC9": "九號",
    "TC10": "十號",
    "WHOT": "酷熱",
    "WCOLD": "寒冷",
    "WMSGNL": "季風",
    "WL": "山泥",
    "WFIREY": "火險",
    "WFIRER": "火險",
    "WFNTSA": "水浸",
    "WFROST": "霜凍",
    "WTMW": "海嘯",
}

_ICON = {code: f"warn_{code.lower()}.png" for code in _LABEL}

_CANCEL = "CANCEL"
_SIGNAL_NAMES = "一號|三號|八號|九號|十號"
_SIGNAL_TOKENS = ("一號", "三號", "八號", "九號", "十號", "戒備信號")
# "下午6時10分發出一號戒備信號" — keep the whole clock, do not clip the hour.
_ISSUE_CLAUSE = re.compile(
    rf"(?:上午|下午|晚上|中午)?\d{{1,2}}時(?:\d{{1,2}}分)?"
    rf"[^。！？\n]{{0,6}}發出(?:{_SIGNAL_NAMES})(?:戒備信號|強風信號|烈風或暴風信號|颶風信號)?"
)
_CONSIDER_CLAUSE = re.compile(
    rf"(?:屆時|黃昏前後|稍後|即將)?(?:考慮)?發出(?:{_SIGNAL_NAMES})"
    rf"(?:戒備信號|強風信號|烈風或暴風信號|颶風信號)?"
)
_CLOCK = re.compile(r"(上午|下午|晚上|中午)?(\d{1,2})時(?:(\d{1,2})分)?")
_TIP_MAX_CHARS = 22

STRIP_INNER_WIDTH = 760
STRIP_PAD = 12
CHIP_ICON_SIZE = 36
CHIP_ICON_TEXT_GAP = 6
CHIP_GAP_COMFORTABLE = 28
CHIP_GAP_TIGHT = 12
TIP_GAP = 24


@dataclass(frozen=True)
class WarningChip:
    statement: str
    code: str
    label: str
    icon: str
    name: str
    severity: int


@dataclass(frozen=True)
class WarningStrip:
    chips: tuple[WarningChip, ...]
    tip: str | None

    @property
    def active(self) -> bool:
        return bool(self.chips) or bool(self.tip)


@dataclass(frozen=True)
class PlacedChip:
    x: int
    icon_size: int
    show_label: bool
    chip: WarningChip


@dataclass(frozen=True)
class PackedStrip:
    chips: tuple[PlacedChip, ...]
    tip: str | None
    tip_x: int | None
    show_labels: bool
    dropped: tuple[str, ...]


def parse_warnsum(data: dict | list | None) -> tuple[WarningChip, ...]:
    """Return in-force chips, highest severity first.

    Cancelled entries (``actionCode`` or ``code`` equal to ``CANCEL``) are
    dropped. Unknown codes still render, using the statement name as the
    label and a low severity so they lose overflow contests.
    """
    if not isinstance(data, dict):
        return ()
    chips: list[WarningChip] = []
    for statement, body in data.items():
        if not isinstance(body, dict):
            continue
        action = str(body.get("actionCode") or "")
        code = str(body.get("code") or statement)
        if action == _CANCEL or code == _CANCEL:
            continue
        label = _LABEL.get(code) or _LABEL.get(statement) or str(
            body.get("name") or code
        )[:4]
        icon = _ICON.get(code) or _ICON.get(statement) or "na.png"
        severity = _SEVERITY.get(code, _SEVERITY.get(statement, 10))
        chips.append(
            WarningChip(
                statement=statement,
                code=code,
                label=label,
                icon=icon,
                name=str(body.get("name") or label),
                severity=severity,
            )
        )
    chips.sort(key=lambda c: (-c.severity, c.code))
    return tuple(chips)


def _hour_24(period: str, hour: int) -> int:
    if period == "下午":
        return hour + 12 if hour < 12 else hour
    if period == "晚上":
        return hour + 12 if hour < 12 else hour
    if period == "上午" and hour == 12:
        return 0
    if period == "中午":
        return 12 if hour in (0, 12) else hour
    return hour


def _clock_to_24h(match: re.Match[str]) -> str:
    """Render HKO 上午/下午 clocks as 24-hour 時/分, matching the dashboard."""
    hour = _hour_24(match.group(1) or "", int(match.group(2)))
    minute = match.group(3)
    if minute is None:
        return f"{hour:02d}時"
    return f"{hour:02d}時{int(minute):02d}分"


def _normalize_clocks(text: str) -> str:
    return _CLOCK.sub(_clock_to_24h, text)


def _signal_clause(text: str) -> str:
    """Prefer the issue-time clause so '18時10分' is not clipped."""
    match = _ISSUE_CLAUSE.search(text) or _CONSIDER_CLAUSE.search(text)
    if match:
        return match.group(0)
    for sentence in re.split(r"[。！？\n]", text):
        sentence = sentence.strip()
        if sentence and any(token in sentence for token in _SIGNAL_TOKENS):
            return sentence
    return re.split(r"[。！？\n]", text, maxsplit=1)[0].strip()


def extract_tip(swt_data: dict | list | None, chips: Sequence[WarningChip]) -> str | None:
    """One short line from Special Weather Tips, or None.

    Prefers a clause that names a tropical-cyclone signal and its issue
    time (the usual pre-no.1 / pre-no.8 case). 上午/下午 clocks become
    24-hour ``18時10分`` so they match the rest of the panel. Returns None
    when the tip only repeats a chip already on the strip.
    """
    if not isinstance(swt_data, dict):
        return None
    items = swt_data.get("swt") or []
    if not isinstance(items, list) or not items:
        return None
    texts = [item.get("desc") or "" for item in items if isinstance(item, dict)]
    texts = [t.strip() for t in texts if t and t.strip()]
    if not texts:
        return None
    phrase = _normalize_clocks(_signal_clause(texts[0])).strip(" 。；，、")
    if not phrase:
        return None
    if len(phrase) > _TIP_MAX_CHARS:
        phrase = phrase[: _TIP_MAX_CHARS - 1] + "…"
    if _tip_repeats_chips(phrase, chips):
        return None
    return phrase


def _tip_repeats_chips(tip: str, chips: Sequence[WarningChip]) -> bool:
    if not chips:
        return False
    codes = {c.code for c in chips}
    mapping = (
        ("十號", ("TC10",)),
        ("九號", ("TC9",)),
        ("八號", ("TC8NE", "TC8SE", "TC8NW", "TC8SW")),
        ("三號", ("TC3",)),
        ("一號", ("TC1",)),
        ("黑雨", ("WRAINB",)),
        ("紅雨", ("WRAINR",)),
        ("黃雨", ("WRAINA",)),
        ("雷暴", ("WTS",)),
    )
    mentioned = [codes_for for token, codes_for in mapping if token in tip]
    if not mentioned:
        return False
    return all(any(code in codes for code in group) for group in mentioned)


def _chip_width(label: str, icon_size: int, show_label: bool, measure: Callable[[str], int]) -> int:
    if show_label:
        return icon_size + CHIP_ICON_TEXT_GAP + measure(label)
    return icon_size


def _row_width(
    chips: Sequence[WarningChip],
    show_label: bool,
    gap: int,
    icon_size: int,
    measure: Callable[[str], int],
) -> int:
    if not chips:
        return 0
    widths = [_chip_width(c.label, icon_size, show_label, measure) for c in chips]
    return sum(widths) + gap * (len(widths) - 1)


def pack_warning_strip(
    chips: Sequence[WarningChip],
    tip: str | None,
    *,
    measure_label: Callable[[str], int],
    measure_tip: Callable[[str], int],
    inner_width: int = STRIP_INNER_WIDTH,
    icon_size: int = CHIP_ICON_SIZE,
    origin_x: int = STRIP_PAD,
) -> PackedStrip:
    """Place chips on one row. Never wraps.

    Yield order when the row would overflow ``inner_width``:

    1. Drop the special-tip text (chips always beat the tip).
    2. Tighten inter-chip gap from 28 to 12.
    3. Hide labels (icons only).
    4. Drop lowest-severity chips from the right until the row fits.
    """
    remaining = list(chips)
    dropped: list[str] = []

    def fits(items: Sequence[WarningChip], labels: bool, gap: int, use_tip: bool) -> bool:
        width = _row_width(items, labels, gap, icon_size, measure_label)
        if use_tip and tip:
            extra = TIP_GAP + measure_tip(tip) if items else measure_tip(tip)
            width += extra
        return width <= inner_width

    plans = (
        (True, CHIP_GAP_COMFORTABLE, True),
        (True, CHIP_GAP_COMFORTABLE, False),
        (True, CHIP_GAP_TIGHT, False),
        (False, CHIP_GAP_TIGHT, False),
    )
    chosen_labels = True
    chosen_gap = CHIP_GAP_COMFORTABLE
    chosen_tip = tip
    found = False
    for labels, gap, use_tip in plans:
        if fits(remaining, labels, gap, use_tip):
            chosen_labels, chosen_gap = labels, gap
            chosen_tip = tip if use_tip else None
            found = True
            break

    if not found:
        chosen_labels, chosen_gap, chosen_tip = False, CHIP_GAP_TIGHT, None
        while remaining and not fits(remaining, chosen_labels, chosen_gap, False):
            dropped.append(remaining.pop().code)

    placed: list[PlacedChip] = []
    x = origin_x
    for chip in remaining:
        placed.append(
            PlacedChip(
                x=x,
                icon_size=icon_size,
                show_label=chosen_labels,
                chip=chip,
            )
        )
        x += _chip_width(chip.label, icon_size, chosen_labels, measure_label) + chosen_gap

    tip_x = None
    if chosen_tip:
        tip_x = origin_x if not placed else x - chosen_gap + TIP_GAP

    return PackedStrip(
        chips=tuple(placed),
        tip=chosen_tip,
        tip_x=tip_x,
        show_labels=chosen_labels,
        dropped=tuple(dropped),
    )


def _fetch(data_type: str) -> dict:
    response = requests.get(HKO_URL, params={"dataType": data_type, "lang": "tc"})
    response.raise_for_status()
    payload = response.json()
    return payload if isinstance(payload, dict) else {}


def get_warning_strip() -> WarningStrip:
    """Fetch ``warnsum`` + ``swt``. Never raises; empty strip on failure."""
    chips: tuple[WarningChip, ...] = ()
    try:
        chips = parse_warnsum(_fetch("warnsum"))
    except Exception:
        logger.warning("warnsum unavailable - warning strip will omit chips", exc_info=True)

    tip = None
    try:
        tip = extract_tip(_fetch("swt"), chips)
    except Exception:
        logger.warning("swt unavailable - warning strip will omit tip", exc_info=True)

    return WarningStrip(chips=chips, tip=tip)
