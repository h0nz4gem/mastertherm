from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
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
    Přidá binární senzory pro daný config_entry v Home Assistant.
    
    Tato funkce inicializuje nové entity binárních senzorů založené na datech získaných
    z konfiguračního záznamu a přidá je do Home Assistant. Každý senzor je spojen s
    konkrétní funkcionalitou nebo stavem zařízení reprezentovaného třídou HeatPump.
    
    Args:
        hass: Instance HomeAssistant, která poskytuje kontext a metody pro interakci s HA.
        config_entry: Konfigurační záznam pro tuto integraci, obsahuje konfigurační data.
        async_add_entities: Funkce callbacku používaná pro přidání nových entit do HA.
    """
    # Získání instance koordinátora pro tento config_entry.
    coordinator = hass.data[DOMAIN][config_entry.entry_id][DATA]

    new_entities = []

    # Vytvoření instancí binárních senzorů pro různé monitorované funkce a stavy.
    new_entities.append(
        GeneralBinarySensor(coordinator, MONITOR, "Rezim Zima", icon="mdi:snowflake")
    )
    new_entities.append(
        GeneralBinarySensor(
            coordinator, MONITOR, "Rezim Leto", icon="mdi:weather-sunny"
        )
    )

    new_entities.append(RunningBinarySensor(coordinator, MONITOR, "Kompresor"))
    new_entities.append(RunningBinarySensor(coordinator, MONITOR, "Obehove cerpadlo"))
    new_entities.append(RunningBinarySensor(coordinator, MONITOR, "Ventilator"))
    new_entities.append(RunningBinarySensor(coordinator, MONITOR, "Elektrokotel 1"))
    new_entities.append(RunningBinarySensor(coordinator, MONITOR, "Elektrokotel 2"))

    new_entities.append(ProblemBinarySensor(coordinator, MONITOR, "Alarm"))
    new_entities.append(ProblemBinarySensor(coordinator, MONITOR, "3 Alarmy"))
    new_entities.append(
        GeneralBinarySensor(
            coordinator, MONITOR, "Reset 3 Alarmu", icon="mdi:restart-alert"
        )
    )

    new_entities.append(
        GeneralBinarySensor(coordinator, MONITOR, "Odtaveni", icon="mdi:snowflake-melt")
    )
    new_entities.append(
        GeneralBinarySensor(coordinator, MONITOR, "Zapnuto", icon="mdi:power")
    )

    # Přidání vytvořených entit do Home Assistant.
    if new_entities:
        async_add_entities(new_entities)

class BinarySensorBase(CoordinatorEntity, BinarySensorEntity):
    """Základní třída pro všechny binární senzory v této integraci."""

    should_poll = False

    def __init__(self, coordinator, device_type):
        """Inicializace základní třídy binárního senzoru."""
        super().__init__(coordinator)
        self._device_type = device_type
        self._device = self.coordinator.hp.devices[device_type]

    @property
    def device_info(self):
        """Vrátí informace o zařízení pro integraci s Home Assistant."""
        return {"identifiers": {(DOMAIN, self._device.id)}}

    @property
    def available(self) -> bool:
        """Vrátí dostupnost senzoru."""
        return self._device.get_availability()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Zpracování aktualizace od koordinátora."""
        self._device = self.coordinator.hp.devices[self._device_type]
        self.async_write_ha_state()

# Třídy pro specifické typy binárních senzorů (RunningBinarySensor, ProblemBinarySensor, GeneralBinarySensor)
# jsou odvozeny od BinarySensorBase a implementují specifické chování pro každý typ senzoru, včetně
# vlastnosti is_on, která určuje, zda je senzor ve stavu on/off, a vlastnosti icon pro určení ikony senzoru.
class RunningBinarySensor(BinarySensorBase):
    """Running třída pro binární senzory v této integraci."""
    
    device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, coordinator, device_type, name, icon=None):
        """
        Inicializuje instance RunningBinarySensor.
        
        Args:
            coordinator: Instance koordinátora, který spravuje aktualizace dat.
            device_type: Typ zařízení, ke kterému senzor patří.
            name: Lidsky čitelný název senzoru.
            icon: Volitelná ikona pro senzor.
        """
        super().__init__(coordinator, device_type)

        self._id = name.replace(" ", "_").casefold()
        self._attr_name = name
        self._attr_unique_id = self._device.id + "_" + self._id
        self.entity_id = "binary_sensor." + self._device.id + "_" + self._id

        self._icon = icon

    @property
    def is_on(self):
        """
        Určuje, zda je zařízení v provozu.
        
        Returns:
            True, pokud je zařízení v provozu, jinak False.
        """
        return self._device.get_state(self._id)

    @property
    def icon(self):
        """
        Vrátí ikonu senzoru.
        
        Returns:
            Řetězec určující ikonu pro senzor.
        """
        return self._icon


class ProblemBinarySensor(BinarySensorBase):
    """Problem třída pro binární senzory v této integraci."""

    device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator, device_type, name, icon=None):
        """
        Inicializuje instance ProblemBinarySensor.
        
        Args:
            coordinator: Instance koordinátora, který spravuje aktualizace dat.
            device_type: Typ zařízení, ke kterému senzor patří.
            name: Lidsky čitelný název senzoru.
            icon: Volitelná ikona pro senzor.
        """
        super().__init__(coordinator, device_type)

        self._id = name.replace(" ", "_").casefold()
        self._attr_name = name
        self._attr_unique_id = self._device.id + "_" + self._id
        self.entity_id = "binary_sensor." + self._device.id + "_" + self._id

        self._icon = icon

    @property
    def is_on(self):
        """
        Určuje, zda je zařízení v provozu.
        
        Returns:
            True, pokud je zařízení v provozu, jinak False.
        """
        return self._device.get_state(self._id)

    @property
    def icon(self):
        """
        Vrátí ikonu senzoru.
        
        Returns:
            Řetězec určující ikonu pro senzor.
        """
        return self._icon

class GeneralBinarySensor(BinarySensorBase):
    """Obecná třída pro binární senzory v této integraci."""

    def __init__(self, coordinator, device_type, name, icon=None):
        """
        Inicializuje instance GeneralBinarySensor.
        
        Args:
            coordinator: Instance koordinátora, který spravuje aktualizace dat.
            device_type: Typ zařízení, ke kterému senzor patří.
            name: Lidsky čitelný název senzoru.
            icon: Volitelná ikona pro senzor.
        """
        super().__init__(coordinator, device_type)

        self._id = name.replace(" ", "_").casefold()
        self._attr_name = name
        self._attr_unique_id = self._device.id + "_" + self._id
        self.entity_id = "binary_sensor." + self._device.id + "_" + self._id

        self._icon = icon

    @property
    def is_on(self):
        """
        Určuje, zda je zařízení v provozu.
        
        Returns:
            True, pokud je zařízení v provozu, jinak False.
        """
        return self._device.get_state(self._id)

    @property
    def icon(self):
        """
        Vrátí ikonu senzoru.
        
        Returns:
            Řetězec určující ikonu pro senzor.
        """
        return self._icon
