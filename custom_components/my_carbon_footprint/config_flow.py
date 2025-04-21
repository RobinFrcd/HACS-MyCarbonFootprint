"""Config flow for My Carbon Footprint integration."""

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector

from .const import CONF_CARBON_INTENSITY, CONF_ENERGY_ENTITIES, DOMAIN


def validate_input(hass: HomeAssistant, user_input: dict[str, Any]) -> dict[str, str]:
    """Validate the user input."""
    errors = {}
    carbon_intensity_entity = user_input[CONF_CARBON_INTENSITY]
    energy_entities = user_input[CONF_ENERGY_ENTITIES]

    # Check if entities exist
    if not hass.states.get(carbon_intensity_entity):
        errors[CONF_CARBON_INTENSITY] = "entity_not_found"

    for entity_id in energy_entities:
        if not hass.states.get(entity_id):
            errors[CONF_ENERGY_ENTITIES] = "entity_not_found"
            break

    return errors


def get_schema(defaults: dict[str, Any]) -> vol.Schema:
    """Get the schema with the given defaults."""
    carbon_intensity_selector = selector.EntitySelector(
        selector.EntitySelectorConfig(
            domain=["sensor"],
            multiple=False,
        )
    )

    energy_entities_selector = selector.EntitySelector(
        selector.EntitySelectorConfig(
            domain=["sensor"],
            multiple=True,
        )
    )

    return vol.Schema(
        {
            vol.Required(
                CONF_CARBON_INTENSITY,
                default=defaults.get(CONF_CARBON_INTENSITY, ""),
            ): carbon_intensity_selector,
            vol.Required(
                CONF_ENERGY_ENTITIES,
                default=defaults.get(CONF_ENERGY_ENTITIES, []),
            ): energy_entities_selector,
        }
    )


class CarbonFootprintConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for My Carbon Footprint."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return CarbonFootprintOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        errors = {}
        defaults = {
            CONF_CARBON_INTENSITY: "",
            CONF_ENERGY_ENTITIES: [],
        }

        if user_input is not None:
            errors = validate_input(self.hass, user_input)
            if not errors:
                return self.async_create_entry(
                    title="My Carbon Footprint",
                    data=user_input,
                )
            defaults = user_input

        return self.async_show_form(
            step_id="user",
            data_schema=get_schema(defaults),
            errors=errors,
        )


class CarbonFootprintOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for My Carbon Footprint."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}
        defaults = {
            CONF_CARBON_INTENSITY: self.config_entry.data.get(
                CONF_CARBON_INTENSITY, ""
            ),
            CONF_ENERGY_ENTITIES: self.config_entry.data.get(CONF_ENERGY_ENTITIES, []),
        }

        if user_input is not None:
            errors = validate_input(self.hass, user_input)
            if not errors:
                return self.async_create_entry(
                    title="",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="init",
            data_schema=get_schema(defaults),
            errors=errors,
        )
