"""The My Carbon Footprint integration."""

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from custom_components.my_carbon_footprint.models import CoordinatorData, EnergySensor

from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)
STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}.coordinator_data"


class CarbonFootprintCoordinator(DataUpdateCoordinator[CoordinatorData]):
    """Class to manage fetching carbon footprint data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.entry: ConfigEntry = entry
        self.carbon_intensity_entity: str = entry.data["carbon_intensity_entity"]
        self.energy_entities: list[str] = entry.data["energy_entities"]
        self.hass: HomeAssistant = hass
        self._previous_energy_values: dict[str, float] = {}
        self._total_carbon: float = 0  # Running total of carbon footprint
        self._entity_carbon: dict[str, float] = {}  # Running totals per entity

        # Initialize storage for persistent data
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )

    async def async_setup(self):
        """Load stored data when coordinator is set up."""
        stored_data = await self._store.async_load()
        if stored_data:
            _LOGGER.debug("Loading stored carbon footprint data: %s", stored_data)
            self._total_carbon = stored_data.get("total_carbon", 0)
            self._entity_carbon = stored_data.get("entity_carbon", {})
            self._previous_energy_values = stored_data.get("previous_energy_values", {})

    async def _async_update_data(self) -> CoordinatorData | None:
        """Fetch data from sensors."""
        try:
            carbon_intensity = self._get_carbon_intensity()
            if carbon_intensity is None:
                return None

            result = CoordinatorData(
                carbon_intensity=carbon_intensity,
                energy_sensors={},
                total_carbon=self._total_carbon,
            )

            current_update_carbon = 0

            for energy_entity_id in self.energy_entities:
                energy_value = self._get_energy_value(energy_entity_id)
                if energy_value is None:
                    continue

                prev_value = self._previous_energy_values.get(energy_entity_id)

                self._previous_energy_values[energy_entity_id] = energy_value

                if prev_value is None:
                    # We need two measurements to calculate consumption
                    result.energy_sensors[energy_entity_id] = EnergySensor(
                        value=0,
                        carbon=self._entity_carbon.get(energy_entity_id, 0),
                    )
                    continue

                # Calculate consumption since last update (in kWh)
                consumption = max(
                    0, energy_value - prev_value
                )  # Ensure non-negative value

                # Calculate carbon footprint (carbon intensity is in g/kWh)
                carbon = (consumption * carbon_intensity) / 1000  # Convert to kg of CO2

                # Update running totals
                entity_total = self._entity_carbon.get(energy_entity_id, 0) + carbon
                self._entity_carbon[energy_entity_id] = entity_total
                current_update_carbon += carbon

                result.energy_sensors[energy_entity_id] = EnergySensor(
                    value=consumption,
                    carbon=entity_total,
                )

            # Update total carbon footprint
            self._total_carbon += current_update_carbon
            result.total_carbon = self._total_carbon

            # Save data to persistent storage
            await self._store.async_save(
                {
                    "total_carbon": self._total_carbon,
                    "entity_carbon": self._entity_carbon,
                    "previous_energy_values": self._previous_energy_values,
                }
            )

            _LOGGER.debug(f"Carbon footprint result: {result}")

            return result

        except Exception as err:
            raise UpdateFailed(f"Error updating carbon footprint: {err}") from err

    def _get_carbon_intensity(self) -> float | None:
        """Get carbon intensity value from the entity."""
        if not self.carbon_intensity_entity:
            return None

        state = self.hass.states.get(self.carbon_intensity_entity)
        if not state:
            _LOGGER.error(
                "Carbon intensity entity %s not found", self.carbon_intensity_entity
            )
            return None

        try:
            return float(state.state)
        except (ValueError, TypeError):
            _LOGGER.error(
                "Unable to convert carbon intensity value to float: %s", state.state
            )
            return None

    def _get_energy_value(self, entity_id: str) -> float | None:
        """Get energy consumption value from an entity."""
        state = self.hass.states.get(entity_id)
        if not state:
            _LOGGER.error("Energy entity %s not found", entity_id)
            return None

        if state.state in ("unknown", "unavailable"):
            _LOGGER.warning("Energy entity %s has state %s", entity_id, state.state)
            return None

        try:
            return float(state.state)
        except (ValueError, TypeError):
            _LOGGER.error("Unable to convert energy value to float: %s", state.state)
            return None
