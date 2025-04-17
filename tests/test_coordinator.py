"""Test CarbonFootprintCoordinator functionality."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.my_carbon_footprint.CarbonFootprintCoordinator import (
    CarbonFootprintCoordinator,
)


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    return MagicMock(
        data={
            "carbon_intensity_entity": "sensor.carbon_intensity",
            "energy_entities": ["sensor.energy1", "sensor.energy2"],
        },
        entry_id="test_entry_id",
    )


async def test_coordinator_initialization(hass: HomeAssistant, mock_config_entry):
    """Test coordinator initialization."""
    coordinator = CarbonFootprintCoordinator(hass, mock_config_entry)

    assert coordinator.carbon_intensity_entity == "sensor.carbon_intensity"
    assert coordinator.energy_entities == ["sensor.energy1", "sensor.energy2"]
    assert coordinator._previous_energy_values == {}
    assert coordinator._total_carbon == 0
    assert coordinator._entity_carbon == {}


async def test_coordinator_update_with_no_previous_values(
    hass: HomeAssistant, mock_config_entry
):
    """Test coordinator update when there are no previous energy values."""
    coordinator = CarbonFootprintCoordinator(hass, mock_config_entry)

    # Create mock state objects
    carbon_mock = MagicMock()
    carbon_mock.state = "100"  # 100g CO2/kWh

    energy1_mock = MagicMock()
    energy1_mock.state = "10"  # 10 kWh

    energy2_mock = MagicMock()
    energy2_mock.state = "20"  # 20 kWh

    # Patch the hass.states.get method directly
    with patch("homeassistant.core.StateMachine.get") as mock_get:

        def side_effect(entity_id):
            return {
                "sensor.carbon_intensity": carbon_mock,
                "sensor.energy1": energy1_mock,
                "sensor.energy2": energy2_mock,
            }.get(entity_id)

        mock_get.side_effect = side_effect

        data = await coordinator._async_update_data()

        assert data is not None
        assert data["carbon_intensity"] == 100
        assert data["total_carbon"] == 0  # No carbon calculated in first update
        assert data["energy_sensors"]["sensor.energy1"]["value"] == 0
        assert data["energy_sensors"]["sensor.energy2"]["value"] == 0

        # Check that previous values were stored
        assert coordinator._previous_energy_values["sensor.energy1"] == 10
        assert coordinator._previous_energy_values["sensor.energy2"] == 20


async def test_coordinator_update_with_consumption(
    hass: HomeAssistant, mock_config_entry
):
    """Test coordinator update with previous energy values."""
    coordinator = CarbonFootprintCoordinator(hass, mock_config_entry)
    coordinator._previous_energy_values = {"sensor.energy1": 10, "sensor.energy2": 20}

    # Create mock state objects
    carbon_mock = MagicMock()
    carbon_mock.state = "100"  # 100g CO2/kWh

    energy1_mock = MagicMock()
    energy1_mock.state = "15"  # 15 kWh (5 kWh increase)

    energy2_mock = MagicMock()
    energy2_mock.state = "30"  # 30 kWh (10 kWh increase)

    # Patch the hass.states.get method directly
    with patch("homeassistant.core.StateMachine.get") as mock_get:

        def side_effect(entity_id):
            return {
                "sensor.carbon_intensity": carbon_mock,
                "sensor.energy1": energy1_mock,
                "sensor.energy2": energy2_mock,
            }.get(entity_id)

        mock_get.side_effect = side_effect

        data = await coordinator._async_update_data()

        assert data is not None
        assert data["carbon_intensity"] == 100
        # 5 kWh * 100 g/kWh + 10 kWh * 100 g/kWh = 1.5 kg CO2
        assert data["total_carbon"] == 1.5
        assert data["energy_sensors"]["sensor.energy1"]["value"] == 5
        assert data["energy_sensors"]["sensor.energy2"]["value"] == 10
        assert data["energy_sensors"]["sensor.energy1"]["carbon"] == 0.5
        assert data["energy_sensors"]["sensor.energy2"]["carbon"] == 1.0

        # Check that previous values were updated
        assert coordinator._previous_energy_values["sensor.energy1"] == 15
        assert coordinator._previous_energy_values["sensor.energy2"] == 30


async def test_coordinator_invalid_carbon_intensity(
    hass: HomeAssistant, mock_config_entry
):
    """Test coordinator handles invalid carbon intensity value."""
    coordinator = CarbonFootprintCoordinator(hass, mock_config_entry)

    # Create mock state objects
    carbon_mock = MagicMock()
    carbon_mock.state = "unknown"

    # Patch the hass.states.get method directly
    with patch("homeassistant.core.StateMachine.get") as mock_get:
        mock_get.return_value = carbon_mock

        data = await coordinator._async_update_data()
        assert data is None


async def test_coordinator_invalid_energy_value(hass: HomeAssistant, mock_config_entry):
    """Test coordinator handles invalid energy value."""
    coordinator = CarbonFootprintCoordinator(hass, mock_config_entry)
    coordinator._previous_energy_values = {
        "sensor.energy1": 10,
    }

    # Create mock state objects
    carbon_mock = MagicMock()
    carbon_mock.state = "100"

    energy1_mock = MagicMock()
    energy1_mock.state = "15"

    energy2_mock = MagicMock()
    energy2_mock.state = "unavailable"

    # Patch the hass.states.get method directly
    with patch("homeassistant.core.StateMachine.get") as mock_get:

        def side_effect(entity_id):
            return {
                "sensor.carbon_intensity": carbon_mock,
                "sensor.energy1": energy1_mock,
                "sensor.energy2": energy2_mock,
            }.get(entity_id)

        mock_get.side_effect = side_effect

        data = await coordinator._async_update_data()

        assert data is not None
        assert "sensor.energy1" in data["energy_sensors"]
        assert "sensor.energy2" not in data["energy_sensors"]


async def test_coordinator_update_failed(hass: HomeAssistant, mock_config_entry):
    """Test UpdateFailed exception is raised on error."""
    coordinator = CarbonFootprintCoordinator(hass, mock_config_entry)

    # Use MagicMock for the get method and set side_effect to raise an exception
    mock_get = MagicMock(side_effect=Exception("Test error"))

    # Patch with context manager
    with (
        patch("homeassistant.core.StateMachine.get", new=mock_get),
        pytest.raises(UpdateFailed),
    ):
        await coordinator._async_update_data()
