"""Platform for sensor integration."""
from __future__ import annotations

from typing import Any

# These constants are relevant to the type of entity we are using.
# See below for how they are used.
from homeassistant.components.number import (
    NumberEntity,
    NumberDeviceClass,
)

from homeassistant.const import ( 
    UnitOfTemperature
)

from .const import DOMAIN
import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add number for passed config_entry in HA."""
    hp = hass.data[DOMAIN][config_entry.entry_id].hp

    new_entities = []

    new_entities.append(TemperatureNumber(hp.devices["regulator"], "Teplota prepnuti Leto", "(0,2,83,-20,30)", min_temp=0, max_temp=20, icon="mdi:sun-thermometer-outline"))
    new_entities.append(TemperatureNumber(hp.devices["regulator"], "Teplota prepnuti Zima", "(0,2,82,-20,30)", min_temp=0, max_temp=20, icon="mdi:snowflake-thermometer"))

    new_entities.append(TemperatureNumber(hp.devices["regulator"], "Topna voda bod A", "(0,2,37,20.0,50.0)", min_temp=30, max_temp=50, icon="mdi:thermometer-chevron-down"))
    new_entities.append(TemperatureNumber(hp.devices["regulator"], "Topna voda bod B", "(0,2,38,20.0,50.0)", min_temp=30, max_temp=50, icon="mdi:thermometer-chevron-up"))
    
    new_entities.append(TemperatureNumber(hp.devices["regulator"], "Teplota povoleni elektrokotle", "(0,2,39,-20.0,30.0)", min_temp=-10, max_temp=10, icon="mdi:thermometer"))

    if new_entities:
        async_add_entities(new_entities)

class NumberBase(NumberEntity):
    """Representation of a dummy Number."""

    # Our dummy class is PUSH, so we tell HA that it should not be polled
    should_poll = False

    def __init__(self, device) -> None:
        """Initialize the sensor."""
        # Usual setup is done here. Callbacks are added in async_added_to_hass.
        self._device = device

    @property
    def device_info(self):
        """Return information to link this entity with the correct device."""
        return {"identifiers": {(DOMAIN, self._device._id)}}

    # This property is important to let HA know if this entity is online or not.
    # If an entity is offline (return False), the UI will refelect this.
    @property
    def available(self) -> bool:
        """Return True if device is available."""
        return self._device.get_availability()

    async def async_added_to_hass(self):
        """Run when this Entity has been added to HA."""
        # Sensors should also register callbacks to HA when their state changes
        self._device.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        """Entity being removed from hass."""
        # The opposite of async_added_to_hass. Remove any registered call backs here.
        self._device.remove_callback(self.async_write_ha_state)
    
class TemperatureNumber(NumberBase):
    """Representation of a Number."""
    device_class = NumberDeviceClass.TEMPERATURE
    # unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, device, name, key, min_temp, max_temp, icon=None):
        """Initialize the sensor."""
        super().__init__(device)
        
        self._id = name.replace(" ","_").casefold()
        self._attr_name = name
        self._attr_unique_id = self._device._id + "_" + self._id
        self.entity_id = "number." + self._device._id + "_" + self._id
        
        self._key = key

        self._attr_native_max_value = max_temp
        self._attr_native_min_value = min_temp
        self._attr_native_step = 0.5
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

        self._icon = icon
    
    @property
    def state(self):
        """Return the state of the number."""
        return self._device.get_state(self._id)

    @property
    def icon(self):
        """Return the icon of the number."""
        return self._icon

    async def async_set_native_value(self, new_value: float) -> None:
        """Set the value of the number.."""
        _LOGGER.debug("%s : async_set_native_value volano s hodnotou: %s", self.entity_id, new_value)

        _LOGGER.debug('%s : volani Heat Pump async_upload_data', self.entity_id)
        await self._device.async_upload_data(self._key, new_value)
        _LOGGER.debug('volani Heat Pump async_upload_data probehlo uspesne')

        _LOGGER.debug("async_set_native_value zpracovano")
