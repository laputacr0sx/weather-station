"""Parser and overflow-packing tests for the HKO warning strip."""
from weather_display.lib.util.warnings import (
    CHIP_GAP_TIGHT,
    CHIP_ICON_SIZE,
    CHIP_ICON_TEXT_GAP,
    STRIP_INNER_WIDTH,
    STRIP_PAD,
    WarningStrip,
    extract_tip,
    pack_warning_strip,
    parse_warnsum,
)


def _warnsum(*pairs):
    """``(statement, code, action)`` rows. action defaults to ISSUE."""
    payload = {}
    for item in pairs:
        statement, code = item[0], item[1]
        action = item[2] if len(item) > 2 else "ISSUE"
        extra = {}
        if statement == "WRAIN":
            extra["type"] = {"WRAINA": "黃色", "WRAINR": "紅色", "WRAINB": "黑色"}[code]
        payload[statement] = {
            "name": code,
            "code": code,
            "actionCode": action,
            **extra,
        }
    return payload


def _measure_label(text: str) -> int:
    # Cubic_11 at 24px is 26px per CJK cell (黃雨 = 52).
    return 26 * len(text)


def _measure_tip(text: str) -> int:
    return 15 * len(text)


def _pack(chips, tip=None, **kwargs):
    return pack_warning_strip(
        chips,
        tip,
        measure_label=_measure_label,
        measure_tip=_measure_tip,
        **kwargs,
    )


def test_empty_warnsum_yields_no_chips():
    assert parse_warnsum({}) == ()
    assert parse_warnsum(None) == ()
    assert parse_warnsum([]) == ()


def test_cancelled_entries_are_dropped():
    data = _warnsum(
        ("WTS", "WTS", "CANCEL"),
        ("WRAIN", "WRAINA", "ISSUE"),
        ("WTCSGNL", "CANCEL", "ISSUE"),
    )
    chips = parse_warnsum(data)
    assert [c.code for c in chips] == ["WRAINA"]


def test_multiple_warnings_sort_by_severity():
    data = _warnsum(
        ("WTS", "WTS"),
        ("WRAIN", "WRAINB"),
        ("WL", "WL"),
        ("WTCSGNL", "TC8NE"),
        ("WFNTSA", "WFNTSA"),
        ("WHOT", "WHOT"),
    )
    chips = parse_warnsum(data)
    assert [c.code for c in chips] == [
        "TC8NE",
        "WRAINB",
        "WL",
        "WTS",
        "WHOT",
        "WFNTSA",
    ]
    assert [c.label for c in chips] == ["八號", "黑雨", "山泥", "雷暴", "酷熱", "水浸"]


def test_two_chips_keep_labels_and_tip():
    chips = parse_warnsum(_warnsum(("WRAIN", "WRAINA"), ("WTS", "WTS")))
    packed = _pack(chips, tip="黃昏或考慮發出一號")
    assert packed.show_labels is True
    assert packed.tip == "黃昏或考慮發出一號"
    assert packed.dropped == ()
    assert [p.chip.code for p in packed.chips] == ["WRAINA", "WTS"]
    assert packed.chips[1].x > packed.chips[0].x


def test_six_chips_keep_labels_and_drop_the_tip():
    chips = parse_warnsum(
        _warnsum(
            ("WTCSGNL", "TC8NE"),
            ("WRAIN", "WRAINB"),
            ("WTS", "WTS"),
            ("WL", "WL"),
            ("WFNTSA", "WFNTSA"),
            ("WMSGNL", "WMSGNL"),
        )
    )
    packed = _pack(chips, tip="沙德爾殘餘靠近，黃昏或考慮發出一號")
    assert len(packed.chips) == 6
    assert packed.show_labels is True
    assert packed.tip is None
    assert packed.dropped == ()
    last = packed.chips[-1]
    right_edge = (
        last.x + CHIP_ICON_SIZE + CHIP_ICON_TEXT_GAP + _measure_label("季風")
    )
    assert right_edge <= STRIP_PAD + STRIP_INNER_WIDTH


def test_eight_chips_fall_back_to_icons_only():
    chips = parse_warnsum(
        _warnsum(
            ("WTCSGNL", "TC8NE"),
            ("WRAIN", "WRAINB"),
            ("WTS", "WTS"),
            ("WL", "WL"),
            ("WFNTSA", "WFNTSA"),
            ("WMSGNL", "WMSGNL"),
            ("WHOT", "WHOT"),
            ("WFIRE", "WFIRER"),
        )
    )
    packed = _pack(chips, tip="will not fit")
    assert len(packed.chips) == 8
    assert packed.show_labels is False
    assert packed.tip is None
    assert packed.dropped == ()
    assert all(p.show_label is False for p in packed.chips)


def test_overflow_drops_lowest_severity_last():
    chips = parse_warnsum(
        _warnsum(("WTCSGNL", "TC10"), ("WRAIN", "WRAINB"), ("WTS", "WTS"))
    )
    packed = _pack(chips, inner_width=CHIP_ICON_SIZE * 2 + CHIP_GAP_TIGHT, icon_size=36)
    # icon-only two chips plus the tight gap fit; third is dropped.
    assert [p.chip.code for p in packed.chips] == ["TC10", "WRAINB"]
    assert packed.dropped == ("WTS",)


def test_extract_tip_prefers_signal_clause():
    swt = {
        "swt": [
            {
                "desc": (
                    "沙德爾的殘餘正為雷州半島至海南島一帶帶來不穩定天氣。"
                    "天文台會視乎其發展及與本港的距離，屆時考慮發出一號戒備信號。"
                )
            }
        ]
    }
    tip = extract_tip(swt, chips=())
    assert tip is not None
    assert "一號" in tip
    assert "雷州半島" not in tip


def test_extract_tip_keeps_24h_issue_time():
    """HKO writes 下午6時10分; the strip uses 18時10分 like the rest of the panel.

    A tight ``.{0,6}`` window around 一號 used to clip this to 時10分發出….
    """
    swt = {
        "swt": [
            {
                "desc": (
                    "沙德爾的殘餘正橫過海南島東南沿岸一帶，並預料會在短期內再度"
                    "增強為熱帶低氣壓。天文台會在下午6時10分發出一號戒備信號。\n"
                    "預料沙德爾會在明日至星期三橫過南海北部。"
                )
            }
        ]
    }
    assert extract_tip(swt, chips=()) == "18時10分發出一號戒備信號"


def test_extract_tip_converts_morning_clock():
    swt = {"swt": [{"desc": "天文台會在上午9時05分發出三號強風信號。"}]}
    assert extract_tip(swt, chips=()) == "09時05分發出三號強風信號"


def test_extract_tip_omitted_when_it_only_repeats_chips():
    chips = parse_warnsum(_warnsum(("WTS", "WTS")))
    swt = {"swt": [{"desc": "雷暴警告現正生效。市民應避免戶外活動。"}]}
    assert extract_tip(swt, chips) is None


def test_extract_tip_kept_when_it_names_a_future_signal():
    chips = parse_warnsum(_warnsum(("WRAIN", "WRAINA"), ("WTS", "WTS")))
    swt = {"swt": [{"desc": "黃昏前後考慮發出一號戒備信號。"}]}
    tip = extract_tip(swt, chips)
    assert tip is not None
    assert "一號" in tip


def test_inactive_strip():
    assert WarningStrip(chips=(), tip=None).active is False
    assert WarningStrip(chips=parse_warnsum(_warnsum(("WTS", "WTS"))), tip=None).active
