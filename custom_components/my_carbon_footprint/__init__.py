"""The My Carbon Footprint integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall

from custom_components.my_carbon_footprint.CarbonFootprintCoordinator import (
    CarbonFootprintCoordinator,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up My Carbon Footprint from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = CarbonFootprintCoordinator(hass, entry)
    await coordinator.async_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Register services
    async def handle_reset_counter(call: ServiceCall) -> None:
        """Handle the reset counter service call."""
        energy_entity_id = call.data.get("energy_entity_id")

        for entry_id, coordinator in hass.data[DOMAIN].items():
            if energy_entity_id:
                # Reset only the specified entity
                if energy_entity_id in coordinator._previous_energy_values:
                    _LOGGER.debug("Resetting counter for %s", energy_entity_id)
                    coordinator._previous_energy_values.pop(energy_entity_id)
            else:
                # Reset all entities
                _LOGGER.debug("Resetting all counters")
                coordinator._previous_energy_values = {}

        # Force data update
        for coordinator in hass.data[DOMAIN].values():
            await coordinator.async_refresh()

    hass.services.async_register(DOMAIN, "reset_counter", handle_reset_counter)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
