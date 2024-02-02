"""Platform for sensor integration."""
from homeassistant.components.button import (
    ButtonEntity,
    ButtonDeviceClass,
)

from homeassistant.helpers.entity import ( 
    DeviceInfo,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
import logging
_LOGGER = logging.getLogger(__name__)

# This function is called as part of the __init__.async_setup_entry (via the
# hass.config_entries.async_forward_entry_setup call)
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add sensors for passed config_entry in HA."""
    hp = hass.data[DOMAIN][config_entry.entry_id].hp
    
    new_entities = []

    new_entities.append(DownloadButton(hp.devices["monitor"], "Aktualizace stavu", icon="mdi:download-box"))
    new_entities.append(DownloadButton(hp.devices["regulator"], "Aktualizace stavu", icon="mdi:download-box"))
    new_entities.append(RestartButton(hp.devices["regulator"], "Restart 3 Alarmu", icon="mdi:restart-alert"))

    if new_entities:
        async_add_entities(new_entities)

class ButtonBase(ButtonEntity):
    """Base representation of a Button."""

    should_poll = False

    def __init__(self, device):
        """Initialize the binary sensor."""
        self._device = device

    async def async_added_to_hass(self):
        """Run when this Entity has been added to HA."""
        # Sensors should also register callbacks to HA when their state changes
        self._device.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        """Entity being removed from hass."""
        # The opposite of async_added_to_hass. Remove any registered call backs here.
        self._device.remove_callback(self.async_write_ha_state)

class DownloadButton(ButtonBase):
    """Base representation of a Button."""

    should_poll = False
    device_class = ButtonDeviceClass.UPDATE

    def __init__(self, device, name, icon=None):
        """Initialize the sensor."""
        self._device = device

        self._id = name.replace(" ","_").casefold()
        self._attr_name = name
        self._attr_unique_id = self._device._id + "_" + self._id
        self.entity_id = "button." + self._device._id + "_" + self._id

        self._icon = icon

    # To link this entity to the cover device, this property must return an
    # identifiers value matching that used in the cover, but no other information such
    # as name. If name is returned, this entity will then also become a device in the
    # HA UI.
    @property
    def device_info(self) -> DeviceInfo:
        """Return information to link this entity with the correct device."""
        return {
            "identifiers": {(DOMAIN, self._device._id)},
            "name": self._device.name,
            "model": self._device.model,
            "sw_version": self._device.firmware_version,
            "manufacturer": self._device.hp.manufacturer,
        }
    
    @property
    def icon(self):
        """Return the icon of the button."""
        return self._icon
    
    async def async_press(self) -> None:
        """Update device sensors."""
        _LOGGER.debug("%s : async_press volano", self.entity_id)

        _LOGGER.debug('%s : volani Heat Pump async_get_availability', self.entity_id)
        if await self._device.hp.async_get_availability():
            _LOGGER.debug('%s : Heat Pump je dostupny', self.entity_id)
            _LOGGER.debug('%s : volani Heat Pump async_fetch_data', self.entity_id)
            await self._device.async_fetch_data()
            _LOGGER.debug('volani Heat Pump async_fetch_data probehlo uspesne')
        
        _LOGGER.debug("async_press zpracovano")

class RestartButton(ButtonBase):
    """Base representation of a Button."""

    should_poll = False
    device_class = ButtonDeviceClass.RESTART

    def __init__(self, device, name, icon=None):
        """Initialize the sensor."""
        self._device = device

        self._id = name.replace(" ","_").casefold()
        self._attr_name = name
        self._attr_unique_id = self._device._id + "_" + self._id
        self.entity_id = "button." + self._device._id + "_" + self._id

        self._icon = icon

    # To link this entity to the cover device, this property must return an
    # identifiers value matching that used in the cover, but no other information such
    # as name. If name is returned, this entity will then also become a device in the
    # HA UI.
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
    
    @property
    def icon(self):
        """Return the icon of the button."""
        return self._icon
    
    async def async_press(self) -> None:
        """Restart 3 alarm."""
        _LOGGER.debug("%s : async_press volano", self.entity_id)

        key = "(0,1,19,0,1)"
        _LOGGER.debug('%s : volani Heat Pump async_upload_data', self.entity_id)
        await self._regulator.async_upload_data(key, 1)
        _LOGGER.debug('volani Heat Pump async_upload_data probehlo uspesne')

        _LOGGER.debug("async_press zpracovano")





