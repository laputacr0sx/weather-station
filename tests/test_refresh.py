"""The panel refreshes for rain and warnings, and otherwise waits."""
from datetime import datetime, timedelta

from weather_display.lib.util.rainfall_nowcast import HomeNowcast, NowcastSlot
from weather_display.refresh import GlassFacts, decide_refresh, rain_attention


def _facts(attention="quiet", warnings=(), known=True):
    return GlassFacts(attention, warnings, known)


def _nowcast(amounts, base):
    slots = []
    cumulative = 0.0
    for index, amount in enumerate(amounts):
        cumulative += amount
        slots.append(
            NowcastSlot(
                ended_at=base + timedelta(minutes=30 * (index + 1)),
                cumulative_mm=cumulative,
                per_slot_mm=amount,
            )
        )
    return HomeNowcast(base_at=base, lat=22.43, lon=114.221, slots=slots)


def test_rain_attention_matches_what_the_glass_says():
    base = datetime(2026, 10, 23, 8, 0)
    when = datetime(2026, 10, 23, 8, 10)
    assert rain_attention(None, when) == "missing"
    assert rain_attention(_nowcast([0, 0, 0, 0], base), when) == "quiet"
    assert rain_attention(_nowcast([0.2, 0, 0, 0], base), when) == "quiet"
    assert rain_attention(_nowcast([0.5, 0, 0, 0], base), when) == "rain"
    assert rain_attention(_nowcast([10, 0, 0, 0], base), when) == "heavy"
    assert rain_attention(_nowcast([0, 0, 0, 0], base), datetime(2026, 10, 23, 10, 0)) == "stale"


def test_first_reading_publishes():
    now = datetime(2026, 10, 23, 5, 0)
    assert decide_refresh(now, None, "", (), _facts()) == "first"


def test_quiet_day_waits_an_hour_and_night_waits_two():
    start = datetime(2026, 10, 23, 5, 0)
    assert decide_refresh(start + timedelta(minutes=15), start, "quiet", (), _facts()) == "keep"
    assert decide_refresh(start + timedelta(hours=1), start, "quiet", (), _facts()) == "due"
    night = datetime(2026, 10, 23, 1, 0)
    assert decide_refresh(night + timedelta(hours=1), night, "quiet", (), _facts()) == "keep"
    assert decide_refresh(night + timedelta(hours=2), night, "quiet", (), _facts()) == "due"


def test_real_rain_updates_about_every_half_hour():
    start = datetime(2026, 10, 23, 15, 0)
    later = start + timedelta(minutes=15)
    assert decide_refresh(later, start, "rain", (), _facts("rain")) == "keep"
    half = start + timedelta(minutes=30)
    assert decide_refresh(half, start, "rain", (), _facts("rain")) == "due"


def test_a_change_the_family_must_see_updates_after_the_floor():
    start = datetime(2026, 10, 23, 9, 0)
    too_soon = start + timedelta(minutes=5)
    assert decide_refresh(too_soon, start, "quiet", (), _facts("rain")) == "keep"
    ready = start + timedelta(minutes=15)
    assert decide_refresh(ready, start, "quiet", (), _facts("rain")) == "urgent"
    assert decide_refresh(ready, start, "quiet", (), _facts("stale")) == "urgent"
    warned = _facts("quiet", ("黃色暴雨警告信號",))
    assert decide_refresh(ready, start, "quiet", (), warned) == "urgent"
    cleared = start + timedelta(minutes=15)
    assert decide_refresh(cleared, start, "quiet", ("黃色暴雨警告信號",), _facts()) == "urgent"


def test_a_failed_reading_is_not_news():
    start = datetime(2026, 10, 23, 9, 0)
    ready = start + timedelta(minutes=15)
    assert decide_refresh(ready, start, "rain", (), _facts("missing")) == "keep"
    assert decide_refresh(ready, start, "quiet", ("黃色暴雨警告信號",), _facts(known=False)) == "keep"


def test_hour_still_arrives_when_the_tick_is_slightly_early():
    start = datetime(2026, 10, 23, 5, 0)
    early = start + timedelta(minutes=58)
    assert decide_refresh(early, start, "quiet", (), _facts()) == "due"
