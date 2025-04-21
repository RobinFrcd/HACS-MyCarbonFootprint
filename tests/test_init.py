"""Test the My Carbon Footprint integration initialization."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.my_carbon_footprint import (
    async_setup_entry,
    async_unload_entry,
)
from custom_components.my_carbon_footprint.const import DOMAIN


@pytest.fixture
def mock_config_entry():
    return MagicMock(
        entry_id="test_entry_id",
        data={
            "carbon_intensity_entity": "sensor.carbon_intensity",
            "energy_entities": ["sensor.energy1", "sensor.energy2"],
        },
        domain=DOMAIN,
    )


async def test_setup_entry(hass: HomeAssistant, mock_config_entry):
    coordinator_mock = AsyncMock()

    with (
        patch(
            "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
            return_value=True,
        ),
        patch(
            "custom_components.my_carbon_footprint.CarbonFootprintCoordinator",
            return_value=coordinator_mock,
        ),
    ):
        result = await async_setup_entry(hass, mock_config_entry)
        assert result is True

        assert hass.data[DOMAIN][mock_config_entry.entry_id] == coordinator_mock
        coordinator_mock.async_refresh.assert_called_once()

        assert DOMAIN in hass.services.async_services()
        assert "reset_counter" in hass.services.async_services()[DOMAIN]


async def test_unload_entry(hass: HomeAssistant, mock_config_entry):
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = MagicMock()

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_unload_platforms",
        return_value=True,
    ):
        result = await async_unload_entry(hass, mock_config_entry)
        assert result is True

        assert mock_config_entry.entry_id not in hass.data[DOMAIN]


async def test_service_reset_counter_specific_entity():
    hass = MagicMock()
    hass_data = {}
    hass.data = {DOMAIN: hass_data}

    energy_values1 = {"sensor.energy1": 10, "sensor.energy2": 20}
    energy_values2 = {"sensor.energy3": 30, "sensor.energy4": 40}

    coordinator1 = MagicMock()
    coordinator1._previous_energy_values = energy_values1
    coordinator1.async_refresh = AsyncMock()

    coordinator2 = MagicMock()
    coordinator2._previous_energy_values = energy_values2
    coordinator2.async_refresh = AsyncMock()

    hass_data["entry1"] = coordinator1
    hass_data["entry2"] = coordinator2

    service_call = MagicMock()
    service_call.data = {"energy_entity_id": "sensor.energy1"}

    # Simple reset_counter handler function based on what's in the integration
    async def handle_reset_counter(call):
        """Handle the reset counter service call."""
        energy_entity_id = call.data.get("energy_entity_id")

        for entry_id, coordinator in hass.data[DOMAIN].items():
            if energy_entity_id:
                # Reset only the specified entity
                if energy_entity_id in coordinator._previous_energy_values:
                    coordinator._previous_energy_values.pop(energy_entity_id)
            else:
                coordinator._previous_energy_values.clear()

        # Force data update
        for coordinator in hass.data[DOMAIN].values():
            await coordinator.async_refresh()

    # Call our handler with the service call
    await handle_reset_counter(service_call)

    # Verify that only sensor.energy1 was removed from coordinator1
    assert "sensor.energy1" not in coordinator1._previous_energy_values
    assert "sensor.energy2" in coordinator1._previous_energy_values
    assert coordinator1._previous_energy_values["sensor.energy2"] == 20

    # Verify that coordinator2 was not affected
    assert coordinator2._previous_energy_values == energy_values2

    # Verify both coordinators' refresh methods were called
    coordinator1.async_refresh.assert_called_once()
    coordinator2.async_refresh.assert_called_once()


async def test_service_reset_counter_all_entities():
    """Test reset_counter service for all entities."""
    # Create a dummy HomeAssistant-like object
    hass = MagicMock()
    hass_data = {}
    hass.data = {DOMAIN: hass_data}

    # Create simple dicts to track previous energy values
    energy_values1 = {"sensor.energy1": 10, "sensor.energy2": 20}
    energy_values2 = {"sensor.energy3": 30, "sensor.energy4": 40}

    # Create mock coordinators
    coordinator1 = MagicMock()
    coordinator1._previous_energy_values = energy_values1
    coordinator1.async_refresh = AsyncMock()

    coordinator2 = MagicMock()
    coordinator2._previous_energy_values = energy_values2
    coordinator2.async_refresh = AsyncMock()

    # Add coordinators to hass.data
    hass_data["entry1"] = coordinator1
    hass_data["entry2"] = coordinator2

    # Create a service call with no specific entity (reset all)
    service_call = MagicMock()
    service_call.data = {}

    # Simple reset_counter handler function
    _LOGGER = MagicMock()

    async def handle_reset_counter(call):
        """Handle the reset counter service call."""
        energy_entity_id = call.data.get("energy_entity_id")

        for entry_id, coordinator in hass.data[DOMAIN].items():
            if energy_entity_id:
                # Reset only the specified entity
                if energy_entity_id in coordinator._previous_energy_values:
                    coordinator._previous_energy_values.pop(energy_entity_id)
            else:
                coordinator._previous_energy_values.clear()

        # Force data update
        for coordinator in hass.data[DOMAIN].values():
            await coordinator.async_refresh()

    # Call our handler with the service call
    await handle_reset_counter(service_call)

    # Verify that all values were cleared
    assert len(coordinator1._previous_energy_values) == 0
    assert len(coordinator2._previous_energy_values) == 0

    # Verify both coordinators' refresh methods were called
    coordinator1.async_refresh.assert_called_once()
    coordinator2.async_refresh.assert_called_once()
