"""MasterTherm integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, Config

from .heat_pump import HeatPump
from .coordinator import HeatPumpCoordinator
from .const import DOMAIN

# List of platforms to support. There should be a matching .py file for each.
PLATFORMS: list[str] = ["sensor", "binary_sensor", "button", "number", "water_heater"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MasterTherm from a config entry."""
    # Store an instance of the "connecting" class that does the work of speaking
    # with your actual devices.

    hp = HeatPump(hass, entry.data["ip_address"])
    coordinator = HeatPumpCoordinator(hass, hp)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await coordinator.async_config_entry_first_refresh()

    # await coordinator.async_refresh()

    # This creates each HA object for each platform your device requires.
    # It's done by calling the `async_setup_entry` function in each platform module.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # This is called when an entry/configured device is to be removed. The class
    # needs to unload itself, and remove callbacks. See the classes for further
    # details
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok