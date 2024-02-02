"""Platform for binary sensor integration."""
# This file shows the setup for the binary sensors associated with the Monitor device.
# They are setup in the same way with the call to the async_setup_entry function
# via HA from the module __init__. Each binary sensor has a device_class, this tells HA how
# to display it in the UI (for know types).

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)

from .const import DOMAIN

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    hp = hass.data[DOMAIN][config_entry.entry_id].hp

    new_entities = []

    new_entities.append(GeneralBinarySensor(hp.devices["monitor"], "Rezim Zima", icon="mdi:snowflake"))
    new_entities.append(GeneralBinarySensor(hp.devices["monitor"], "Rezim Leto", icon="mdi:weather-sunny"))

    new_entities.append(RunningBinarySensor(hp.devices["monitor"], "Kompresor"))
    new_entities.append(RunningBinarySensor(hp.devices["monitor"], "Obehove cerpadlo"))
    new_entities.append(RunningBinarySensor(hp.devices["monitor"], "Ventilator"))
    new_entities.append(RunningBinarySensor(hp.devices["monitor"], "Elektrokotel 1"))
    new_entities.append(RunningBinarySensor(hp.devices["monitor"], "Elektrokotel 2"))
    
    new_entities.append(ProblemBinarySensor(hp.devices["monitor"], "Alarm"))
    new_entities.append(ProblemBinarySensor(hp.devices["monitor"], "3 Alarmy"))
    new_entities.append(GeneralBinarySensor(hp.devices["monitor"], "Reset 3 Alarmu", icon="mdi:restart-alert"))
    
    new_entities.append(GeneralBinarySensor(hp.devices["monitor"], "Odtaveni", icon="mdi:snowflake-melt"))
    new_entities.append(GeneralBinarySensor(hp.devices["monitor"], "Zapnuto", icon="mdi:power"))

    if new_entities:
        async_add_entities(new_entities)


# This base class shows the common properties and methods for a binary sensor.
class BinarySensorBase(BinarySensorEntity):
    """Base representation of a Binary Sensor."""

    should_poll = False

    def __init__(self, device):
        """Initialize the binary sensor."""
        self._device = device

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

    async def async_added_to_hass(self):
        """Run when this Entity has been added to HA."""
        # Sensors should also register callbacks to HA when their state changes
        self._device.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        """Entity being removed from hass."""
        # The opposite of async_added_to_hass. Remove any registered call backs here.
        self._device.remove_callback(self.async_write_ha_state)


class RunningBinarySensor(BinarySensorBase):
    """Representation of a Binary Sensor."""
    device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, device, name, icon=None):
        """Initialize the sensor."""
        super().__init__(device)

        self._id = name.replace(" ","_").casefold()
        self._attr_name = name
        self._attr_unique_id = self._device._id + "_" + self._id
        self.entity_id = "binary_sensor." + self._device._id + "_" + self._id

        self._icon = icon

    @property
    def is_on(self):
        """Return the state of the sensor."""
        return self._device.get_state(self._id)

    @property
    def icon(self):
        """Return the icon of the binary sensor."""
        return self._icon

class ProblemBinarySensor(BinarySensorBase):
    """Representation of a Binary Sensor."""
    device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, device, name, icon=None):
        """Initialize the sensor."""
        super().__init__(device)
        
        self._id = name.replace(" ","_").casefold()
        self._attr_name = name
        self._attr_unique_id = self._device._id + "_" + self._id
        self.entity_id = "binary_sensor." + self._device._id + "_" + self._id

        self._icon = icon

    @property
    def is_on(self):
        """Return the state of the sensor."""
        return self._device.get_state(self._id)
    
    @property
    def icon(self):
        """Return the icon of the sensor."""
        return self._icon

class GeneralBinarySensor(BinarySensorBase):
    """Representation of a Binary Sensor."""

    def __init__(self, device, name, icon=None):
        """Initialize the sensor."""
        super().__init__(device)

        self._id = name.replace(" ","_").casefold()
        self._attr_name = name
        self._attr_unique_id = self._device._id + "_" + self._id
        self.entity_id = "binary_sensor." + self._device._id + "_" + self._id

        self._icon = icon

    @property
    def is_on(self):
        """Return the state of the sensor."""
        return self._device.get_state(self._id)
    
    @property
    def icon(self):
        """Return the icon of the sensor."""
        return self._icon





