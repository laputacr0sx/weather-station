"""Decide when a full-color refresh is worth the time it takes.

The Spectra 6 panel spends about 20 seconds on every update, so the
Lifebook checks on the timer and only replaces ``current.png`` when the
picture the family sees should change. The Pi already skips the glass
when that file is unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from weather_display.lib.render.home_dashboard import _HEAVY_MM, _UMBRELLA_MM, _is_current

# Never flash the panel twice inside this window, including an urgent change.
FLOOR = timedelta(minutes=10)
# While the home cell expects real rain, the countdown on the glass moves.
RAIN_EVERY = timedelta(minutes=30)
# Dry daytime. Each page then stays up for about an hour.
DAY_EVERY = timedelta(hours=1)
# Overnight, unless rain or a warning changes.
NIGHT_EVERY = timedelta(hours=2)
# Timer jitter (AccuracySec plus RandomizedDelaySec) can land a tick early.
_GRACE = timedelta(minutes=2)


@dataclass(frozen=True)
class GlassFacts:
    """What the refresh compares. Pixel noise such as the clock minute is absent."""

    attention: str
    warnings: tuple[str, ...] = ()
    warnings_known: bool = True


def rain_attention(nowcast, when: datetime) -> str:
    """Collapse the nowcast into the change the family can see.

    Dry and trace rain share ``quiet``: both stay on a white band, and a
    trace must not pull the panel forward. A failed download is ``missing``
    and is not treated as news.
    """
    if nowcast is None:
        return "missing"
    if not _is_current(nowcast, when):
        return "stale"
    peak = nowcast.peak_per_slot_mm
    if peak >= _HEAVY_MM:
        return "heavy"
    if peak >= _UMBRELLA_MM:
        return "rain"
    return "quiet"


def decide_refresh(
    now: datetime,
    last_at: datetime | None,
    last_attention: str,
    last_warnings: tuple[str, ...],
    facts: GlassFacts,
) -> str:
    """Return ``first``, ``due``, ``urgent``, or ``keep``.

    ``due`` is the slow interval and swaps the page. ``urgent`` is a rain
    or warning change and keeps the page already on the glass.
    """
    if last_at is None:
        return "first"
    if not facts.warnings_known:
        return "keep"
    elapsed = now - last_at
    if elapsed < FLOOR:
        return "keep"
    attention_changed = (
        facts.attention != last_attention and facts.attention != "missing"
    )
    warnings_changed = facts.warnings != last_warnings
    interval = _interval(now, facts.attention)
    if elapsed + _GRACE >= interval:
        return "due"
    if attention_changed or warnings_changed:
        return "urgent"
    return "keep"


def _interval(now: datetime, attention: str) -> timedelta:
    if attention in {"rain", "heavy"}:
        return RAIN_EVERY
    if now.hour < 5:
        return NIGHT_EVERY
    return DAY_EVERY


def load_refresh(path: Path) -> tuple[datetime | None, str, tuple[str, ...]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None, "", ()
    if not lines:
        return None, "", ()
    try:
        refreshed_at = datetime.fromisoformat(lines[0])
    except ValueError:
        return None, "", ()
    attention = lines[1] if len(lines) > 1 else ""
    warnings = tuple(line for line in lines[2:] if line)
    return refreshed_at, attention, warnings


def save_refresh(path: Path, when: datetime, facts: GlassFacts) -> None:
    names = [name.replace("\n", " ").strip() for name in facts.warnings]
    body = "\n".join([when.isoformat(timespec="seconds"), facts.attention, *names])
    path.write_text(body + "\n", encoding="utf-8")
