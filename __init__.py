from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .heat_pump import HeatPump
from .coordinator import HeatPumpCoordinator
from .const import (
    DOMAIN,
    DATA,
)

# Seznam platforem, které tato integrace podporuje.
PLATFORMS: list[str] = ["sensor", "binary_sensor", "button", "number", "water_heater"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Asynchronní nastavení konfiguračního záznamu pro integraci.
    Tato funkce inicializuje HeatPump a HeatPumpCoordinator s daty z konfiguračního záznamu.
    Také plánuje první aktualizaci dat a nastavuje podporované platformy.

    Args:
        hass: Instance HomeAssistant.
        entry: Konfigurační záznam, který má být nastaven.

    Returns:
        True, pokud bylo nastavení úspěšné.
    """

    # Vytvoření instance HeatPump s IP adresou získanou z konfiguračního záznamu.
    hp = HeatPump(hass, entry.data["ip_address"])
    
    # Vytvoření a inicializace HeatPumpCoordinator.
    coordinator = HeatPumpCoordinator(hass, hp)

    # Zajistění, že pro tento doménový klíč existuje slovník v hass.data.
    hass.data.setdefault(DOMAIN, {})

    # Uložení instance koordinátora do hass.data pro snadný přístup.
    hass.data[DOMAIN][entry.entry_id] = {
        DATA: coordinator,
    }

    # Plánování první aktualizace dat.
    await coordinator.async_config_entry_first_refresh()

    # Nastavení podporovaných platforem pro tento konfigurační záznam.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Asynchronní odstranění konfiguračního záznamu pro integraci.
    Tato funkce odstraní všechny platformy spojené s konfiguračním záznamem
    a odebere data z hass.data.

    Args:
        hass: Instance HomeAssistant.
        entry: Konfigurační záznam, který má být odstraněn.

    Returns:
        True, pokud bylo odstranění úspěšné.
    """

    # Asynchronní odstranění všech platforem spojených s tímto konfiguračním záznamem.
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    # Pokud bylo odstranění úspěšné, odeber data spojená s konfiguračním záznamem.
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
