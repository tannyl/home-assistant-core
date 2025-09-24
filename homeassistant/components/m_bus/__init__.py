"""The M-Bus integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .coordinator import MBusCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]

CONFIG_SCHEMA = cv.config_entry_only_config_schema("m_bus")

type MBusConfigEntry = ConfigEntry[MBusCoordinator]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the M-Bus integration."""
    del hass, config  # Unused parameters
    return True


async def async_setup_entry(hass: HomeAssistant, entry: MBusConfigEntry) -> bool:
    """Set up M-Bus from a config entry."""
    coordinator = MBusCoordinator(hass, entry)

    # Store coordinator in runtime_data
    entry.runtime_data = coordinator

    # Perform initial data fetch
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: MBusConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
