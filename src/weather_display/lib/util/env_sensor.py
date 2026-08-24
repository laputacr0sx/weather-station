from dataclasses import dataclass


@dataclass
class EnvironmentData:
    temperature: float
    humidity: float
    pressure: float
