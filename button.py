from homeassistant.components.button import (
    ButtonEntity,
    ButtonDeviceClass,
)

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from homeassistant.core import (
    callback,
)

from homeassistant.helpers.entity import (
    DeviceInfo,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    DATA,
    MONITOR,
    REGULATOR,
)

import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """
    Nastaví tlačítka pro daný konfigurační záznam v Home Assistant.
    
    Tato funkce vytváří instance tlačítek na základě dat z konfiguračního záznamu
    a přidává je do systému Home Assistant. Každé tlačítko reprezentuje akci,
    kterou může uživatel vyvolat, např. aktualizaci dat nebo restart systému.
    """
    # Získání koordinátora z globálních dat.
    coordinator = hass.data[DOMAIN][config_entry.entry_id][DATA]

    new_entities = []

    # Vytvoření a přidání tlačítek pro aktualizaci a restart.
    new_entities.append(
        UpdateButton(coordinator, MONITOR, "Aktualizace stavu", icon="mdi:download-box")
    )
    new_entities.append(
        UpdateButton(
            coordinator, REGULATOR, "Aktualizace stavu", icon="mdi:download-box"
        )
    )
    new_entities.append(
        RestartButton(
            coordinator, REGULATOR, "Restart 3 Alarmu", icon="mdi:restart-alert"
        )
    )

     # Přidání nových entit do Home Assistant.
    if new_entities:
        async_add_entities(new_entities)


class ButtonBase(CoordinatorEntity, ButtonEntity):
    """
    Základní reprezentace tlačítka.
    
    Tato třída dědí z CoordinatorEntity a ButtonEntity a slouží jako základ
    pro specifická tlačítka. Poskytuje základní vlastnosti a metody společné
    pro všechna tlačítka v této integraci.
    """
    should_poll = False

    def __init__(self, coordinator, device_type):
        """Inicializuje základní tlačítko."""
        super().__init__(coordinator)
        self._device_type = device_type
        self._device = self.coordinator.hp.devices[device_type]

    @callback
    def _handle_coordinator_update(self) -> None:
        """Zpracuje aktualizovaná data od koordinátora."""
        self._device = self.coordinator.hp.devices[self._device_type]
        self.async_write_ha_state()

# Definice specifických tříd tlačítek (UpdateButton, RestartButton)...
# Tyto třídy rozšiřují ButtonBase a implementují konkrétní chování a vlastnosti
# pro jednotlivé typy tlačítek, včetně metody async_press, která definuje akci,
# jež se má provést po stisknutí tlačítka.
class UpdateButton(ButtonBase):
    """
    Reprezentace tlačítka pro aktualizaci.
    
    Toto tlačítko slouží k iniciaci aktualizace senzorů nebo jiných dat zařízení. Je založeno na základní třídě ButtonBase
    a rozšiřuje její funkcionalitu o možnost aktualizace.
    """

    should_poll = False
    device_class = ButtonDeviceClass.UPDATE

    def __init__(self, coordinator, device_type, name, icon=None):
        """
        Inicializuje aktualizační tlačítko.
        
        Args:
            coordinator: Koordinátor, který spravuje aktualizace dat.
            device_type: Typ zařízení, ke kterému tlačítko patří.
            name: Lidsky čitelný název tlačítka.
            icon: Volitelná ikona pro tlačítko.
        """
        super().__init__(coordinator, device_type)

        self._id = name.replace(" ", "_").casefold()
        self._attr_name = name
        self._attr_unique_id = self._device.id + "_" + self._id
        self.entity_id = "button." + self._device.id + "_" + self._id

        self._icon = icon

    @property
    def device_info(self) -> DeviceInfo:
        """
        Vrátí informace pro propojení entity se správným zařízením.
        
        Returns:
            DeviceInfo: Slovník s informacemi o zařízení.
        """
        return {
            "identifiers": {(DOMAIN, self._device.id)},
            "name": self._device.name,
            "model": self._device.model,
            "sw_version": self._device.firmware_version,
            "manufacturer": self._device.hp.manufacturer,
        }

    @property
    def icon(self):
        """
        Vrátí ikonu tlačítka.
        
        Returns:
            str: Identifikátor ikony.
        """
        return self._icon

    async def async_press(self) -> None:
        """
        Spustí akci aktualizace senzorů nebo dat zařízení.
        
        Tato metoda je volána, když uživatel stiskne tlačítko v uživatelském rozhraní.
        """

        _LOGGER.debug("%s : volani Coordinator async_set_updated_data", self.entity_id)
        await self.coordinator.async_set_updated_data()


class RestartButton(ButtonBase):
    """
    Reprezentace tlačítka pro restart.
    
    Toto tlačítko slouží k restartu zařízení. Je založeno na základní třídě ButtonBase.
    """

    should_poll = False
    device_class = ButtonDeviceClass.RESTART

    def __init__(self, coordinator, device_type, name, icon=None):
        """
        Inicializuje restart tlačítko.
        
        Args:
            coordinator: Koordinátor, který spravuje aktualizace dat.
            device_type: Typ zařízení, ke kterému tlačítko patří.
            name: Lidsky čitelný název tlačítka.
            icon: Volitelná ikona pro tlačítko.
        """
        super().__init__(coordinator, device_type)

        self._id = name.replace(" ", "_").casefold()
        self._attr_name = name
        self._attr_unique_id = self._device.id + "_" + self._id
        self.entity_id = "button." + self._device.id + "_" + self._id

        self._icon = icon

    @property
    def device_info(self):
        """Vrátí informace o zařízení pro integraci s Home Assistant."""
        return {"identifiers": {(DOMAIN, self._device.id)}}

    @property
    def available(self) -> bool:
        """Vrátí dostupnost senzoru."""
        return self._device.get_availability()

    @property
    def icon(self):
        """
        Vrátí ikonu tlačítka.
        
        Returns:
            str: Identifikátor ikony.
        """
        return self._icon

    async def async_press(self) -> None:
        """
        Spustí akci restart zařízení a následně aktualizuje senzory.
        
        Tato metoda je volána, když uživatel stiskne tlačítko v uživatelském rozhraní.
        """

        key = "(0,1,19,0,1)"
        _LOGGER.debug("%s : volani Heat Pump async_upload_data", self.entity_id)
        await self._regulator.async_upload_data(key, 1)

        _LOGGER.debug("%s : volani Coordinator async_set_updated_data", self.entity_id)
        await self.coordinator.async_set_updated_data()
