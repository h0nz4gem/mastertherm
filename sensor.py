from homeassistant.const import (
    UnitOfTemperature,
    UnitOfTime,
)

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
)

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from homeassistant.core import (
    callback,
)

from .const import (
    DOMAIN,
    DATA,
    MONITOR,
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """
    Nastaví senzory pro konfigurační záznam v Home Assistant.
    
    Vytváří a přidává senzory pro různé měřené hodnoty tepelného čerpadla,
    jako jsou teploty a doby provozu, do Home Assistant.
    """
    coordinator = hass.data[DOMAIN][config_entry.entry_id][DATA]

    new_entities = []

    new_entities.append(TemperatureSensor(coordinator, MONITOR, "Teplota topne vody"))
    new_entities.append(TemperatureSensor(coordinator, MONITOR, "Venkovni teplota"))
    new_entities.append(
        TemperatureSensor(coordinator, MONITOR, "Zadana teplota topne vody")
    )
    new_entities.append(
        TemperatureSensor(coordinator, MONITOR, "Rychle nastaveni topne vody")
    )
    new_entities.append(
        GeneralSensor(
            coordinator, MONITOR, "Nastaveni EEV", icon="mdi:pipe-valve", unit="%"
        )
    )

    new_entities.append(TemperatureSensor(coordinator, MONITOR, "Venku bod A"))
    new_entities.append(TemperatureSensor(coordinator, MONITOR, "Topna voda bod A"))
    new_entities.append(TemperatureSensor(coordinator, MONITOR, "Venku bod B"))
    new_entities.append(TemperatureSensor(coordinator, MONITOR, "Topna voda bod B"))
    new_entities.append(
        TemperatureSensor(coordinator, MONITOR, "Teplota povoleni elektrokotle")
    )

    new_entities.append(
        GeneralSensor(
            coordinator, MONITOR, "Hodiny kompresoru", icon="mdi:counter", unit="hod"
        )
    )
    new_entities.append(
        GeneralSensor(
            coordinator, MONITOR, "Starty kompresoru", icon="mdi:counter", unit="x10"
        )
    )
    new_entities.append(
        GeneralSensor(
            coordinator, MONITOR, "Hodiny cerpadla", icon="mdi:counter", unit="hod"
        )
    )
    new_entities.append(
        GeneralSensor(
            coordinator, MONITOR, "Cas od odtaveni", icon="mdi:counter", unit="min"
        )
    )

    new_entities.append(TemperatureSensor(coordinator, MONITOR, "TO1 Skutecna teplota"))
    new_entities.append(
        GeneralSensor(
            coordinator,
            MONITOR,
            "TO1 Analogovy vystup",
            icon="mdi:pipe-valve",
            unit="%",
        )
    )

    new_entities.append(TemperatureSensor(coordinator, MONITOR, "TO3 Skutecna teplota"))

    if new_entities:
        async_add_entities(new_entities)


class SensorBase(CoordinatorEntity, SensorEntity):
    """
    Základní třída pro všechny senzory v integraci.
    
    Poskytuje společné vlastnosti a metody pro senzory, včetně dostupnosti a aktualizace dat.
    """
    should_poll = False

    def __init__(self, coordinator, device_type):
        """Inicializuje základní senzorovou entitu."""
        super().__init__(coordinator)
        self._device_type = device_type
        self._device = self.coordinator.hp.devices[device_type]

    @property
    def device_info(self):
        """Vrací informace o zařízení pro integraci s Home Assistant."""
        return {"identifiers": {(DOMAIN, self._device.id)}}

    @property
    def available(self) -> bool:
        """Vrací dostupnost senzorové entity."""
        return self._device.get_availability()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Zpracovává aktualizaci dat z koordinátora."""
        self._device = self.coordinator.hp.devices[self._device_type]
        self.async_write_ha_state()


class TemperatureSensor(SensorBase):
    """
    Senzor pro měření teploty.
    
    Zobrazuje teplotní hodnoty v Home Assistant s příslušnou jednotkou a ikonou.
    """
    device_class = SensorDeviceClass.TEMPERATURE

    def __init__(self, coordinator, device_type, name, icon=None):
        """Inicializuje teplotní senzorovou entitu."""
        super().__init__(coordinator, device_type)

        self._id = name.replace(" ", "_").casefold()
        self._attr_name = name
        self._attr_unique_id = self._device.id + "_" + self._id
        self.entity_id = "sensor." + self._device.id + "_" + self._id

        self._icon = icon
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def state(self):
        """Vrací aktuální nastavenou teplotu."""
        return self._device.get_state(self._id)

    @property
    def icon(self):
        """Vrací ikonu entity."""
        return self._icon


class GeneralSensor(SensorBase):
    """
    Obecný senzor pro zobrazení různých dat.
    
    Umožňuje zobrazení dat bez specifické třídy senzoru, například počet hodin provozu.
    """

    def __init__(self, coordinator, device_type, name, icon=None, unit=None):
        """Inicializuje obecnou senzorovou entitu."""
        super().__init__(coordinator, device_type)

        self._id = name.replace(" ", "_").casefold()
        self._attr_name = name
        self._attr_unique_id = self._device.id + "_" + self._id
        self.entity_id = "sensor." + self._device.id + "_" + self._id

        self._icon = icon
        self._attr_native_unit_of_measurement = unit

    @property
    def state(self):
        """Vrací aktuální nastavenou hodnotu."""
        return self._device.get_state(self._id)

    @property
    def icon(self):
        """Vrací ikonu entity."""
        return self._icon