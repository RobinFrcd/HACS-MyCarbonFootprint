"""Sensor platform for My Carbon Footprint integration."""

from __future__ import annotations

import logging
from typing import Any, cast

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import CarbonFootprintCoordinator
from .const import DOMAIN, ICON_CARBON, NAME

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the carbon footprint sensors."""
    coordinator = cast(CarbonFootprintCoordinator, hass.data[DOMAIN][entry.entry_id])

    entities = []

    # Add total carbon footprint sensor
    entities.append(CarbonFootprintSensor(coordinator, entry))

    # Add individual energy carbon footprint sensors
    for entity_id in coordinator.energy_entities:
        entities.append(EnergyCarbonFootprintSensor(coordinator, entry, entity_id))

    async_add_entities(entities)


class CarbonFootprintSensor(
    CoordinatorEntity[CarbonFootprintCoordinator], SensorEntity
):
    """Sensor for total carbon footprint."""

    _attr_device_class = None
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = "kg CO2"
    _attr_has_entity_name = True
    _attr_icon = ICON_CARBON

    def __init__(
        self, coordinator: CarbonFootprintCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_total_carbon"
        self._attr_name = "Total Carbon Footprint"
        self.coordinator = coordinator

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=NAME,
            manufacturer="Home Assistant Community",
            model="Carbon Footprint Calculator",
            sw_version="0.1.0",
        )

    @property
    def native_value(self) -> float:
        """Return the carbon footprint value."""
        if not self.coordinator.data:
            return 0

        return self.coordinator.data["total_carbon"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if not self.coordinator.data:
            return {}

        return {
            "carbon_intensity": self.coordinator.data["carbon_intensity"],
            "energy_sensors": len(self.coordinator.energy_entities),
        }


class EnergyCarbonFootprintSensor(
    CoordinatorEntity[CarbonFootprintCoordinator], SensorEntity
):
    """Sensor for individual energy source carbon footprint."""

    _attr_device_class = None
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = "kg CO2"
    _attr_has_entity_name = True
    _attr_icon = ICON_CARBON

    def __init__(
        self,
        coordinator: CarbonFootprintCoordinator,
        entry: ConfigEntry,
        energy_entity_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._energy_entity_id = energy_entity_id
        self.coordinator = coordinator

        # Extract the entity name from the entity_id
        # (e.g., sensor.living_room_energy becomes living_room_energy)
        entity_name = energy_entity_id.split(".")[-1]

        self._attr_unique_id = f"{entry.entry_id}_{entity_name}_carbon"
        self._attr_name = f"{entity_name.replace('_', ' ').title()} Carbon Footprint"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=NAME,
            manufacturer="Home Assistant Community",
            model="Carbon Footprint Calculator",
            sw_version="0.1.0",
        )

    @property
    def native_value(self) -> float:
        """Return the carbon footprint value."""
        if not self.coordinator.data or not self.coordinator.data.get("energy_sensors"):
            return 0

        energy_data = self.coordinator.data["energy_sensors"].get(
            self._energy_entity_id
        )
        if not energy_data:
            return 0

        return energy_data["carbon"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if not self.coordinator.data or not self.coordinator.data.get("energy_sensors"):
            return {
                "energy_consumption": 0,
                "carbon_intensity": 0,
                "source_entity": self._energy_entity_id,
            }

        energy_data = self.coordinator.data["energy_sensors"].get(
            self._energy_entity_id, {}
        )

        return {
            "energy_consumption": energy_data.get("value", 0),
            "carbon_intensity": self.coordinator.data.get("carbon_intensity", 0),
            "source_entity": self._energy_entity_id,
        }
