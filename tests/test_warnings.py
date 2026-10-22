from weather_display.lib.util.warnings import parse_warnings


def test_empty_summary_means_no_warning():
    assert parse_warnings({}) == []
    assert parse_warnings(None) == []


def test_cancelled_warning_is_hidden():
    payload = {
        "WTS": {
            "name": "雷暴警告",
            "code": "WTS",
            "actionCode": "CANCEL",
        }
    }
    assert parse_warnings(payload) == []


def test_rainstorm_level_comes_from_the_code():
    payload = {
        "WRAIN": {"name": "黃色暴雨警告信號", "code": "WRAINA", "actionCode": "ISSUE"},
        "WFIRE": {"name": "紅色火災危險警告", "code": "WFIRER", "actionCode": "ISSUE"},
    }
    warnings = parse_warnings(payload)
    assert [item.name for item in warnings] == ["紅色火災危險警告", "黃色暴雨警告信號"]
    assert warnings[0].tone == "red"
    assert warnings[1].tone == "yellow"


def test_black_rainstorm_and_typhoon_signal():
    payload = {
        "WRAIN": {"name": "黑色暴雨警告信號", "code": "WRAINB", "actionCode": "ISSUE"},
        "WTCSGNL": {"name": "八號東南烈風或暴風信號", "code": "TC8SE", "actionCode": "ISSUE"},
    }
    warnings = parse_warnings(payload)
    assert warnings[0].tone == "black"
    assert warnings[1].tone == "red"
