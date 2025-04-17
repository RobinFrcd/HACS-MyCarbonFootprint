"""Test my_carbon_footprint config flow."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.my_carbon_footprint import const
from custom_components.my_carbon_footprint.config_flow import (
    CarbonFootprintConfigFlow,
)
from custom_components.my_carbon_footprint.const import (
    CONF_CARBON_INTENSITY,
    CONF_ENERGY_ENTITIES,
    DOMAIN,
)


# This fixture bypasses the actual setup of the integration
# since we only want to test the config flow. We test the
# actual functionality of the integration in other test modules.
@pytest.fixture()
def bypass_setup():
    """Prevent setup."""
    with patch(
        "custom_components.my_carbon_footprint.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


async def test_show_form(hass: HomeAssistant) -> None:
    """Test that the form is served with no input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_create_entry(hass: HomeAssistant) -> None:
    """Test creating an entry."""
    # Mock that entities exist
    with patch("homeassistant.core.StateMachine.get") as mock_get:
        mock_get.return_value = True  # Entity exists

        # Submit form with valid entities
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={
                CONF_CARBON_INTENSITY: "sensor.carbon_intensity",
                CONF_ENERGY_ENTITIES: ["sensor.energy1", "sensor.energy2"],
            },
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == const.NAME
        assert result["data"] == {
            CONF_CARBON_INTENSITY: "sensor.carbon_intensity",
            CONF_ENERGY_ENTITIES: ["sensor.energy1", "sensor.energy2"],
        }


async def test_form_invalid_carbon_intensity(hass: HomeAssistant) -> None:
    """Test validation of carbon intensity entity."""
    # Mock that carbon intensity entity doesn't exist
    with patch("homeassistant.core.StateMachine.get") as mock_get:

        def get_side_effect(entity_id):
            if entity_id == "sensor.carbon_intensity":
                return None  # Entity doesn't exist
            return True  # Other entities exist

        mock_get.side_effect = get_side_effect

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={
                CONF_CARBON_INTENSITY: "sensor.carbon_intensity",
                CONF_ENERGY_ENTITIES: ["sensor.energy1", "sensor.energy2"],
            },
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {CONF_CARBON_INTENSITY: "entity_not_found"}


async def test_form_invalid_energy_entity(hass: HomeAssistant) -> None:
    """Test validation of energy entities."""
    # Mock that energy entity doesn't exist
    with patch("homeassistant.core.StateMachine.get") as mock_get:

        def get_side_effect(entity_id):
            if entity_id == "sensor.energy1":
                return None  # Entity doesn't exist
            return True  # Other entities exist

        mock_get.side_effect = get_side_effect

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={
                CONF_CARBON_INTENSITY: "sensor.carbon_intensity",
                CONF_ENERGY_ENTITIES: ["sensor.energy1", "sensor.energy2"],
            },
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {CONF_ENERGY_ENTITIES: "entity_not_found"}


async def test_options_flow(hass: HomeAssistant, bypass_setup) -> None:
    """Test options flow."""
    # Mock the validation function to return no errors
    with patch(
        "custom_components.my_carbon_footprint.config_flow.validate_input",
        return_value={},
    ):
        # Set up our config flow handler
        flow = CarbonFootprintConfigFlow()

        # Create a mock config entry
        mock_entry = MagicMock(
            entry_id="test_entry_id",
            data={
                CONF_CARBON_INTENSITY: "sensor.carbon_intensity",
                CONF_ENERGY_ENTITIES: ["sensor.energy1", "sensor.energy2"],
            },
        )

        # Test the options flow by using the config flow's method directly
        options_flow = flow.async_get_options_flow(mock_entry)

        # Pass the hass object to the options flow
        options_flow.hass = hass

        # Initialize the options flow
        result = await options_flow.async_step_init()
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "init"

        # Submit updated options
        result = await options_flow.async_step_init(
            user_input={
                CONF_CARBON_INTENSITY: "sensor.carbon_intensity_updated",
                CONF_ENERGY_ENTITIES: [
                    "sensor.energy1_updated",
                    "sensor.energy2_updated",
                ],
            }
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"] == {
            CONF_CARBON_INTENSITY: "sensor.carbon_intensity_updated",
            CONF_ENERGY_ENTITIES: ["sensor.energy1_updated", "sensor.energy2_updated"],
        }
