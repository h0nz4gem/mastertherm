from __future__ import annotations

from homeassistant.components.number import (
    NumberEntity,
    NumberDeviceClass,
)

from homeassistant.const import UnitOfTemperature

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from homeassistant.core import (
    callback,
)

from .const import (
    DOMAIN,
    DATA,
    REGULATOR,
)

import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """
    Nastaví číselné entity pro konfigurační záznam v Home Assistant.
    
    Tato funkce vytváří nové entity pro nastavení teplotních hodnot
    a přidává je do Home Assistant pomocí koordinátora dat.
    """
    coordinator = hass.data[DOMAIN][config_entry.entry_id][DATA]

    new_entities = []

    # Vytváření instancí TemperatureNumber pro různé teplotní nastavení
    # a přidání do seznamu entit.
    new_entities.append(
        TemperatureNumber(
            coordinator,
            REGULATOR,
            "Teplota prepnuti Leto",
            "(0,2,83,-20,30)",
            min_temp=0,
            max_temp=20,
            icon="mdi:sun-thermometer-outline",
        )
    )
    new_entities.append(
        TemperatureNumber(
            coordinator,
            REGULATOR,
            "Teplota prepnuti Zima",
            "(0,2,82,-20,30)",
            min_temp=0,
            max_temp=20,
            icon="mdi:snowflake-thermometer",
        )
    )

    new_entities.append(
        TemperatureNumber(
            coordinator,
            REGULATOR,
            "Topna voda bod A",
            "(0,2,37,20.0,50.0)",
            min_temp=30,
            max_temp=50,
            icon="mdi:thermometer-chevron-down",
        )
    )
    new_entities.append(
        TemperatureNumber(
            coordinator,
            REGULATOR,
            "Topna voda bod B",
            "(0,2,38,20.0,50.0)",
            min_temp=30,
            max_temp=50,
            icon="mdi:thermometer-chevron-up",
        )
    )

    new_entities.append(
        TemperatureNumber(
            coordinator,
            REGULATOR,
            "Teplota povoleni elektrokotle",
            "(0,2,39,-20.0,30.0)",
            min_temp=-10,
            max_temp=10,
            icon="mdi:thermometer",
        )
    )

    if new_entities:
        async_add_entities(new_entities)
        
class NumberBase(CoordinatorEntity, NumberEntity):
    """
    Základní třída pro číselné entity.
    
    Dědí od CoordinatorEntity a NumberEntity a poskytuje společné vlastnosti
    a metody pro všechny číselné entity v této integraci.
    """
    should_poll = False

    def __init__(self, coordinator, device_type) -> None:
        """Inicializace číselné entity."""
        super().__init__(coordinator)
        self._device_type = device_type
        self._device = self.coordinator.hp.devices[device_type]

    @property
    def device_info(self):
        """Vrací informace o zařízení pro integraci s Home Assistant."""
        return {"identifiers": {(DOMAIN, self._device.id)}}

    @property
    def available(self) -> bool:
        """Vrací dostupnost entity."""
        return self._device.get_availability()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Zpracuje aktualizovaná data od koordinátora."""
        self._device = self.coordinator.hp.devices[self._device_type]
        self.async_write_ha_state()


class TemperatureNumber(NumberBase):
    """
    Entity pro nastavení teplotních hodnot.
    
    Umožňuje uživatelům nastavit specifické teplotní hodnoty pro tepelné čerpadlo
    přes uživatelské rozhraní Home Assistant.
    """
    device_class = NumberDeviceClass.TEMPERATURE

    def __init__(
        self, coordinator, device_type, name, key, min_temp, max_temp, icon=None
    ):
        """Inicializace entity pro nastavení teploty."""
        super().__init__(coordinator, device_type)

        # Nastavení základních vlastností entity
        self._id = name.replace(" ", "_").casefold()
        self._attr_name = name
        self._attr_unique_id = self._device.id + "_" + self._id
        self.entity_id = "number." + self._device.id + "_" + self._id

        self._key = key

        # Nastavení limitů teploty
        self._attr_native_max_value = max_temp
        self._attr_native_min_value = min_temp
        self._attr_native_step = 0.5
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

        self._icon = icon

    @property
    def state(self):
        """Vrací aktuální nastavenou teplotu."""
        return self._device.get_state(self._id)

    @property
    def icon(self):
        """Vrací ikonu entity."""
        return self._icon

    async def async_set_native_value(self, new_value: float) -> None:
        """
        Asynchronně nastaví novou teplotní hodnotu.
        
        Tato metoda volá funkce pro aktualizaci dat tepelného čerpadla,
        následně pomocí koordinátoru aktualizuje hodnoty.
        """
        _LOGGER.debug(
            "%s : async_set_native_value volano s hodnotou: %s",
            self.entity_id,
            new_value,
        )

        _LOGGER.debug("%s : volani Heat Pump async_upload_data", self.entity_id)
        await self._device.async_upload_data(self._key, new_value)

        _LOGGER.debug("%s : volani Coordinator async_set_updated_data", self.entity_id)
        await self.coordinator.async_set_updated_data()
