from dataclasses import dataclass


@dataclass
class EnergySensor:
    value: float
    carbon: float


@dataclass
class CoordinatorData:
    carbon_intensity: float
    energy_sensors: dict[str, EnergySensor]
    total_carbon: float
