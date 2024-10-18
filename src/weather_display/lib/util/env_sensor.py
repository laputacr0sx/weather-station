from dataclasses import dataclass


@dataclass
class EnvironmentData:
    temperature: float
    humidity: float
    pressure: float


def parse_bme280() -> EnvironmentData:
    return EnvironmentData(temperature=25.7, humidity=64.1, pressure=1011.5)


def get_env_data():
    return
