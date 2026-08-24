from weather_display.run import parse_args


def test_parse_args_save_path():
    assert parse_args(["--save", "tests/output/live.png"]).save == "tests/output/live.png"


def test_parse_args_default_is_display():
    assert parse_args([]).save is None
