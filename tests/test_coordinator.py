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
    return MagicMock(
        data={
            "carbon_intensity_entity": "sensor.carbon_intensity",
            "energy_entities": ["sensor.energy1", "sensor.energy2"],
        },
        entry_id="test_entry_id",
    )


async def test_coordinator_initialization(hass: HomeAssistant, mock_config_entry):
    coordinator = CarbonFootprintCoordinator(hass, mock_config_entry)

    assert coordinator.carbon_intensity_entity == "sensor.carbon_intensity"
    assert coordinator.energy_entities == ["sensor.energy1", "sensor.energy2"]
    assert coordinator._previous_energy_values == {}
    assert coordinator._total_carbon == 0
    assert coordinator._entity_carbon == {}


async def test_coordinator_update_with_no_previous_values(
    hass: HomeAssistant, mock_config_entry
):
    coordinator = CarbonFootprintCoordinator(hass, mock_config_entry)

    carbon_mock = MagicMock()
    carbon_mock.state = 100  # 100g CO2/kWh

    energy1_mock = MagicMock()
    energy1_mock.state = 10  # 10 kWh

    energy2_mock = MagicMock()
    energy2_mock.state = 20  # 20 kWh

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
        assert data.carbon_intensity == 100
        assert data.total_carbon == 0  # No carbon calculated in first update
        assert data.energy_sensors["sensor.energy1"].value == 0
        assert data.energy_sensors["sensor.energy2"].value == 0

        # Check that previous values were stored
        assert (
            coordinator._previous_energy_values["sensor.energy1"] == energy1_mock.state
        )
        assert (
            coordinator._previous_energy_values["sensor.energy2"] == energy2_mock.state
        )


async def test_coordinator_update_with_consumption(
    hass: HomeAssistant, mock_config_entry
):
    E1_previous_value = 10
    E1_current_value = 15
    E2_previous_value = 20
    E2_current_value = 30

    coordinator = CarbonFootprintCoordinator(hass, mock_config_entry)
    coordinator._previous_energy_values = {
        "sensor.energy1": E1_previous_value,
        "sensor.energy2": E2_previous_value,
    }

    # Create mock state objects
    carbon_mock = MagicMock()
    carbon_mock.state = 125  # 125g CO2/kWh

    energy1_mock = MagicMock()
    energy1_mock.state = E1_current_value  # 15 kWh (5 kWh increase)

    energy2_mock = MagicMock()
    energy2_mock.state = E2_current_value  # 30 kWh (10 kWh increase)

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
        assert data.carbon_intensity == carbon_mock.state

        assert data.energy_sensors["sensor.energy1"].value == (
            E1_current_value - E1_previous_value
        )
        assert data.energy_sensors["sensor.energy2"].value == (
            E2_current_value - E2_previous_value
        )
        assert (
            data.energy_sensors["sensor.energy1"].carbon
            == (E1_current_value - E1_previous_value) * carbon_mock.state / 1000
        )
        assert (
            data.energy_sensors["sensor.energy2"].carbon
            == (E2_current_value - E2_previous_value) * carbon_mock.state / 1000
        )

        assert (
            data.total_carbon
            == data.energy_sensors["sensor.energy1"].carbon
            + data.energy_sensors["sensor.energy2"].carbon
        )

        # Check that previous values were updated
        assert coordinator._previous_energy_values["sensor.energy1"] == E1_current_value
        assert coordinator._previous_energy_values["sensor.energy2"] == E2_current_value


async def test_coordinator_invalid_carbon_intensity(
    hass: HomeAssistant, mock_config_entry
):
    coordinator = CarbonFootprintCoordinator(hass, mock_config_entry)

    carbon_mock = MagicMock()
    carbon_mock.state = "unknown"

    with patch("homeassistant.core.StateMachine.get") as mock_get:
        mock_get.return_value = carbon_mock

        data = await coordinator._async_update_data()
        assert data is None


async def test_coordinator_invalid_energy_value(hass: HomeAssistant, mock_config_entry):
    coordinator = CarbonFootprintCoordinator(hass, mock_config_entry)
    coordinator._previous_energy_values = {
        "sensor.energy1": 10,
    }

    carbon_mock = MagicMock()
    carbon_mock.state = 125

    energy1_mock = MagicMock()
    energy1_mock.state = 15

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
        assert "sensor.energy1" in data.energy_sensors
        assert "sensor.energy2" not in data.energy_sensors


async def test_coordinator_update_failed(hass: HomeAssistant, mock_config_entry):
    coordinator = CarbonFootprintCoordinator(hass, mock_config_entry)

    mock_get = MagicMock(side_effect=Exception("Test error"))

    with (
        patch("homeassistant.core.StateMachine.get", new=mock_get),
        pytest.raises(UpdateFailed),
    ):
        await coordinator._async_update_data()
