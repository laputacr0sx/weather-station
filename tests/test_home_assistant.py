from weather_display.lib.util.home_assistant import RoomClimate, rooms_from_states


def _state(entity_id, value, friendly_name):
    return {
        "entity_id": entity_id,
        "state": value,
        "attributes": {"friendly_name": friendly_name, "unit_of_measurement": "°C"},
    }


def test_rooms_from_states_pairs_temperature_with_humidity():
    states = {
        "sensor.aqara_temp_humidity_sensor_temperature": _state(
            "sensor.aqara_temp_humidity_sensor_temperature",
            "28.31",
            "Guestroom Core TH 溫度",
        ),
        "sensor.aqara_temp_humidity_sensor_humidity": _state(
            "sensor.aqara_temp_humidity_sensor_humidity",
            "73.62",
            "Guestroom Core TH 濕度",
        ),
        "sensor.aqara_temp_humidity_sensor_temperature_3": _state(
            "sensor.aqara_temp_humidity_sensor_temperature_3",
            "unavailable",
            "Bedroom Core TH 溫度",
        ),
        "sensor.aqara_temp_humidity_sensor_humidity_3": _state(
            "sensor.aqara_temp_humidity_sensor_humidity_3",
            "unknown",
            "Bedroom Core TH 濕度",
        ),
    }

    rooms = rooms_from_states(states)

    assert rooms[0] == RoomClimate("客房", 28.31, 73.62)
    assert rooms[2] == RoomClimate("睡房", None, None)
    assert rooms[1].name == "睡房門口"
    assert rooms[3].name == "客廳"
    assert rooms[4].name == "大門"
    assert rooms[5].name == "露台"
    assert len(rooms) == 6
    assert all(name.isascii() is False for name in (room.name for room in rooms))
