"""Test sensor platform for My Carbon Footprint integration."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.components.sensor import SensorStateClass
from homeassistant.core import HomeAssistant

from custom_components.my_carbon_footprint.const import DOMAIN, ICON_CARBON
from custom_components.my_carbon_footprint.models import CoordinatorData, EnergySensor
from custom_components.my_carbon_footprint.sensor import (
    CarbonFootprintSensor,
    EnergyCarbonFootprintSensor,
    async_setup_entry,
)


@pytest.fixture
def mock_coordinator():
    coordinator = MagicMock()
    coordinator.data = CoordinatorData(
        carbon_intensity=100,
        total_carbon=1.5,
        energy_sensors={
            "sensor.energy1": EnergySensor(value=5, carbon=0.5),
            "sensor.energy2": EnergySensor(value=10, carbon=1.0),
        },
    )
    coordinator.energy_entities = ["sensor.energy1", "sensor.energy2"]
    return coordinator


@pytest.fixture
def mock_config_entry():
    return MagicMock(
        entry_id="test_entry_id",
        data={
            "carbon_intensity_entity": "sensor.carbon_intensity",
            "energy_entities": ["sensor.energy1", "sensor.energy2"],
        },
    )


async def test_sensor_setup():
    # Create a mock HomeAssistant data structure
    hass = MagicMock()
    mock_config_entry = MagicMock(entry_id="test_entry_id")
    mock_coordinator = MagicMock()

    hass.data = {DOMAIN: {mock_config_entry.entry_id: mock_coordinator}}
    mock_coordinator.energy_entities = ["sensor.energy1", "sensor.energy2"]

    entities = []

    def add_entities(new_entities, update_before_add=False):
        entities.extend(new_entities)

    with (
        patch(
            "custom_components.my_carbon_footprint.sensor.CarbonFootprintSensor",
            return_value=MagicMock(),
        ),
        patch(
            "custom_components.my_carbon_footprint.sensor.EnergyCarbonFootprintSensor",
            return_value=MagicMock(),
        ),
    ):
        await async_setup_entry(hass, mock_config_entry, add_entities)

        # Should create 3 entities: 1 for total + 2 for energy entities
        assert len(entities) == 3


async def test_total_carbon_footprint_sensor(
    hass: HomeAssistant, mock_coordinator: MagicMock, mock_config_entry: MagicMock
):
    sensor = CarbonFootprintSensor(mock_coordinator, mock_config_entry)

    # Test entity attributes
    assert sensor.unique_id == mock_config_entry.entry_id + "_total_carbon"
    assert sensor.name == "Total Carbon Footprint"
    assert sensor.icon == ICON_CARBON
    assert sensor.state_class == SensorStateClass.TOTAL_INCREASING
    assert sensor.native_unit_of_measurement == "kg CO2"

    # Test device info
    device_info = sensor.device_info
    assert DOMAIN in str(device_info["identifiers"])
    assert mock_config_entry.entry_id in str(device_info["identifiers"])
    assert device_info["name"] == "My Carbon Footprint"

    # Test state values
    total_carbon = mock_coordinator.data.total_carbon
    assert sensor.native_value == total_carbon

    # Test attributes
    attrs = sensor.extra_state_attributes
    assert attrs["carbon_intensity"] == mock_coordinator.data.carbon_intensity
    assert attrs["energy_sensors"] == len(mock_coordinator.data.energy_sensors)

    # Test with no data
    mock_coordinator.data = None
    assert (
        sensor.native_value == total_carbon
    )  # Keep latest data even if coordinator is empty
    assert sensor.extra_state_attributes == {}


async def test_energy_carbon_footprint_sensor(
    hass: HomeAssistant, mock_coordinator, mock_config_entry
):
    sensor = EnergyCarbonFootprintSensor(
        mock_coordinator, mock_config_entry, "sensor.energy1"
    )

    assert sensor.unique_id == "test_entry_id_energy1_carbon"
    assert sensor.name == "Energy1 Carbon Footprint"
    assert sensor.icon == ICON_CARBON
    assert sensor.state_class == SensorStateClass.TOTAL_INCREASING
    assert sensor.native_unit_of_measurement == "kg CO2"

    device_info = sensor.device_info
    assert DOMAIN in str(device_info["identifiers"])
    assert "test_entry_id" in str(device_info["identifiers"])
    assert device_info["name"] == "My Carbon Footprint"

    # Test state values
    assert sensor.native_value == 0.5

    # Test attributes
    attrs = sensor.extra_state_attributes
    assert attrs["energy_consumption"] == 5
    assert attrs["carbon_intensity"] == 100
    assert attrs["source_entity"] == "sensor.energy1"

    # Test with no data
    mock_coordinator.data = None
    # Keep latest data even if coordinator is empty
    assert sensor.native_value == 0.5

    # Test attributes with no data
    attrs = sensor.extra_state_attributes
    assert attrs["energy_consumption"] == 0
    assert attrs["carbon_intensity"] == 0
    assert attrs["source_entity"] == "sensor.energy1"

    # Test with missing entity data
    mock_coordinator.data = CoordinatorData(
        carbon_intensity=100,
        total_carbon=1.0,
        energy_sensors={
            "sensor.energy2": EnergySensor(value=10, carbon=1.0),
        },
    )
    # Keep latest data even if coordinator is empty
    assert sensor.native_value == 0.5

    # Test attributes with missing entity data
    attrs = sensor.extra_state_attributes
    assert attrs["energy_consumption"] == 0
    assert attrs["carbon_intensity"] == 100
    assert attrs["source_entity"] == "sensor.energy1"
