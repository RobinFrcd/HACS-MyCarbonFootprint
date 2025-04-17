"""Test sensor platform for My Carbon Footprint integration."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.components.sensor import SensorStateClass
from homeassistant.core import HomeAssistant

from custom_components.my_carbon_footprint.const import DOMAIN, ICON_CARBON
from custom_components.my_carbon_footprint.sensor import (
    CarbonFootprintSensor,
    EnergyCarbonFootprintSensor,
    async_setup_entry,
)


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator."""
    coordinator = MagicMock()
    coordinator.data = {
        "carbon_intensity": 100,
        "total_carbon": 1.5,
        "energy_sensors": {
            "sensor.energy1": {"value": 5, "carbon": 0.5},
            "sensor.energy2": {"value": 10, "carbon": 1.0},
        },
    }
    coordinator.energy_entities = ["sensor.energy1", "sensor.energy2"]
    return coordinator


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    return MagicMock(
        entry_id="test_entry_id",
        data={
            "carbon_intensity_entity": "sensor.carbon_intensity",
            "energy_entities": ["sensor.energy1", "sensor.energy2"],
        },
    )


async def test_sensor_setup():
    """Test sensor setup."""
    # Since we're having issues with HomeAssistant, let's test the function directly

    # Create a mock HomeAssistant data structure
    hass = MagicMock()
    mock_config_entry = MagicMock(entry_id="test_entry_id")
    mock_coordinator = MagicMock()

    # Set up the domain in hass.data
    hass.data = {DOMAIN: {mock_config_entry.entry_id: mock_coordinator}}
    mock_coordinator.energy_entities = ["sensor.energy1", "sensor.energy2"]

    # Test our entities directly
    entities = []

    # Mock the add_entities function
    def add_entities(new_entities, update_before_add=False):
        entities.extend(new_entities)

    # Create a combined patch for both sensor classes
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
        # Call setup with our mocks
        await async_setup_entry(hass, mock_config_entry, add_entities)

        # Should create 3 entities: 1 for total + 2 for energy entities
        assert len(entities) == 3


async def test_total_carbon_footprint_sensor(
    hass: HomeAssistant, mock_coordinator, mock_config_entry
):
    """Test the total carbon footprint sensor."""
    sensor = CarbonFootprintSensor(mock_coordinator, mock_config_entry)

    # Test entity attributes
    assert sensor.unique_id == "test_entry_id_total_carbon"
    assert sensor.name == "Total Carbon Footprint"
    assert sensor.icon == ICON_CARBON
    assert sensor.state_class == SensorStateClass.TOTAL_INCREASING
    assert sensor.native_unit_of_measurement == "kg CO2"

    # Test device info
    device_info = sensor.device_info
    assert DOMAIN in str(device_info["identifiers"])
    assert "test_entry_id" in str(device_info["identifiers"])
    assert device_info["name"] == "My Carbon Footprint"

    # Test state values
    assert sensor.native_value == 1.5

    # Test attributes
    attrs = sensor.extra_state_attributes
    assert attrs["carbon_intensity"] == 100
    assert attrs["energy_sensors"] == 2

    # Test with no data
    mock_coordinator.data = None
    assert sensor.native_value == 0
    assert sensor.extra_state_attributes == {}


async def test_energy_carbon_footprint_sensor(
    hass: HomeAssistant, mock_coordinator, mock_config_entry
):
    """Test the energy carbon footprint sensor."""
    sensor = EnergyCarbonFootprintSensor(
        mock_coordinator, mock_config_entry, "sensor.energy1"
    )

    # Test entity attributes
    assert sensor.unique_id == "test_entry_id_energy1_carbon"
    assert sensor.name == "Energy1 Carbon Footprint"
    assert sensor.icon == ICON_CARBON
    assert sensor.state_class == SensorStateClass.TOTAL_INCREASING
    assert sensor.native_unit_of_measurement == "kg CO2"

    # Test device info
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
    assert sensor.native_value == 0

    # Test attributes with no data
    attrs = sensor.extra_state_attributes
    assert attrs["energy_consumption"] == 0
    assert attrs["carbon_intensity"] == 0
    assert attrs["source_entity"] == "sensor.energy1"

    # Test with missing entity data
    mock_coordinator.data = {
        "carbon_intensity": 100,
        "total_carbon": 1.0,
        "energy_sensors": {
            "sensor.energy2": {"value": 10, "carbon": 1.0},
        },
    }
    assert sensor.native_value == 0

    # Test attributes with missing entity data
    attrs = sensor.extra_state_attributes
    assert attrs["energy_consumption"] == 0
    assert attrs["carbon_intensity"] == 100
    assert attrs["source_entity"] == "sensor.energy1"
