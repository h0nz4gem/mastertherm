from homeassistant.const import (
    UnitOfTemperature,
    ATTR_TEMPERATURE,
)

from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
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
    REGULATOR,
)
import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """
    Asynchronní nastavení vstupního bodu integrace vodního tepelného čerpadla.
    """
    coordinator = hass.data[DOMAIN][config_entry.entry_id][DATA]

    new_entities = []

    new_entities.append(
        WaterHeatPump(
            coordinator,
            "Nastaveni rezimu topeni",
            icon="mdi:heat-pump",
        )
    )

    if new_entities:
        async_add_entities(new_entities)


class WaterHeatPump(CoordinatorEntity, WaterHeaterEntity):
    """
    Reprezentace entity vodního tepelného čerpadla v Home Assistant.
    """

    should_poll = False

    def __init__(self, coordinator, name, icon=None):
        """
        Inicializace entity vodního tepelného čerpadla.
        """
        super().__init__(coordinator)
        self._regulator = self.coordinator.hp.devices[REGULATOR]
        self._monitor = self.coordinator.hp.devices[MONITOR]

        self._id = name.replace(" ", "_").casefold()
        self._attr_name = name
        self._attr_unique_id = self._regulator.id + "_" + self._id
        self.entity_id = "water_heater." + self._regulator.id + "_" + self._id

        self._icon = icon

        self._temp_delta = 2.5
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_supported_features = WaterHeaterEntityFeature.OPERATION_MODE
        self._attr_current_operation = None
        self._attr_operation_list = [
            "AUT",
            "Zima",
            "Leto",
            "MAN",
        ]

    @property
    def device_info(self):
        """
        Vrací informace o zařízení pro integraci s Home Assistant.
        """
        return {"identifiers": {(DOMAIN, self._regulator.id)}}

    @property
    def available(self) -> bool:
        """
        Určuje, zda je zařízení dostupné.
        """
        return self._regulator.get_availability()

    @callback
    def _handle_coordinator_update(self) -> None:
        """
        Zpracovává aktualizaci dat z koordinátora a obnovuje stav entity.
        """
        self._regulator = self.coordinator.hp.devices[REGULATOR]
        self._monitor = self.coordinator.hp.devices[MONITOR]
        self.async_write_ha_state()

    @property
    def icon(self):
        """
        Vrací ikonu entity.
        """
        return self._icon

    @property
    def state(self):
        """
        Určuje aktuální stav režimu operace tepelného čerpadla.
        """
        res = self._regulator.get_state("rezim_zima_leto")
        if res == 0:
            if self._attr_current_operation is None:
                self._attr_current_operation = "AUT"
            return "AUT"
        elif res == 1 and self._monitor.get_state("rychle_nastaveni_topne_vody") == 0:
            if self._attr_current_operation is None:
                self._attr_current_operation = "Zima"
            return "Zima"
        elif res == 2:
            if self._attr_current_operation is None:
                self._attr_current_operation = "Leto"
            return "Leto"
        elif res == 1 and self._monitor.get_state("rychle_nastaveni_topne_vody") > 0:
            if self._attr_current_operation is None:
                self._attr_current_operation = "MAN"
            return "MAN"
        else:
            return None

    @property
    def current_temperature(self):
        """
        Vrací aktuální teplotu topné vody.
        """
        return self._monitor.get_state("teplota_topne_vody")

    @property
    def target_temperature(self):
        """
        Vrací cílovou teplotu topné vody na základě aktuálního režimu a nastavení.
        """
        target_rychle = self._monitor.get_state("rychle_nastaveni_topne_vody")
        target_zadana = self._monitor.get_state("zadana_teplota_topne_vody")

        if target_rychle > 0 and self.state == "MAN":
            return target_rychle
        elif target_zadana == 0:
            return None
        else:
            return target_zadana

    @property
    def target_temperature_high(self) -> float | None:
        """
        Vrací horní limit cílové teploty.
        """
        target_temp = self.target_temperature
        if target_temp is None:
            return None
        return target_temp + self._temp_delta

    @property
    def target_temperature_low(self) -> float | None:
        """
        Vrací dolní limit cílové teploty.
        """
        target_temp = self.target_temperature
        if target_temp is None:
            return None
        return target_temp - self._temp_delta

    @property
    def min_temp(self):
        """
        Vrací minimální možnou teplotu nastavení pro tepelné čerpadlo.
        """
        a_temp = self._monitor.get_state("topna_voda_bod_a")
        if a_temp is None:
            return 30
        return a_temp - 5

    @property
    def max_temp(self):
        """
        Vrací maximální možnou teplotu nastavení pro tepelné čerpadlo.
        """
        b_temp = self._monitor.get_state("topna_voda_bod_b")
        if b_temp is None:
            return 50
        return b_temp + 5

    async def async_set_temperature(self, **kwargs):
        """
        Asynchronně nastavuje cílovou teplotu tepelného čerpadla.
        """
        if self.current_operation != "MAN":
            _LOGGER.debug("%s : volani async_set_operation_mode", self.entity_id)
            await self.async_set_operation_mode("MAN")

        _LOGGER.debug(
            "%s : async_set_temperature volano s teplotou: %s.",
            self.entity_id,
            kwargs.get(ATTR_TEMPERATURE),
        )

        key_temp = "(0,2,123,00.0,47.5)"

        _LOGGER.debug("%s : volani Heat Pump async_upload_data", self.entity_id)
        await self._regulator.async_upload_data(key_temp, kwargs.get(ATTR_TEMPERATURE))

        _LOGGER.debug("%s : volani Coordinator async_set_updated_data", self.entity_id)
        await self.coordinator.async_set_updated_data()

    async def async_set_operation_mode(self, operation_mode):
        """
        Asynchronně nastavuje režim operace tepelného čerpadla.
        """

        _LOGGER.debug(
            "%s : async_set_operation_mode volano s modem: %s",
            self.entity_id,
            operation_mode,
        )
        key_mode = "(0,3,50,0,2)"

        if operation_mode == "AUT":
            if self.current_operation == "MAN":
                await self._async_unset_mode_man()
            _LOGGER.debug("%s : volani Heat Pump async_upload_data", self.entity_id)
            await self._regulator.async_upload_data(key_mode, 0)
            self._attr_current_operation = "AUT"
        elif operation_mode == "Zima":
            if self.current_operation == "MAN":
                await self._async_unset_mode_man()
            _LOGGER.debug("%s : volani Heat Pump async_upload_data", self.entity_id)
            await self._regulator.async_upload_data(key_mode, 1)
            self._attr_current_operation = "Zima"
        elif operation_mode == "Leto":
            if self.current_operation == "MAN":
                await self._async_unset_mode_man()
            _LOGGER.debug("%s : volani Heat Pump async_upload_data", self.entity_id)
            await self._regulator.async_upload_data(key_mode, 2)
            self._attr_current_operation = "Leto"
        elif operation_mode == "MAN":
            _LOGGER.debug("%s : volani Heat Pump async_upload_data", self.entity_id)
            await self._regulator.async_upload_data(key_mode, 1)
            self._attr_current_operation = "MAN"
            _LOGGER.debug("%s : volani async_set_temperature", self.entity_id)
            await self.async_set_temperature(
                **{ATTR_TEMPERATURE: self.target_temperature}
            )
            self._attr_supported_features = (
                WaterHeaterEntityFeature.TARGET_TEMPERATURE
                | WaterHeaterEntityFeature.OPERATION_MODE
            )

        _LOGGER.debug("%s : volani Coordinator async_set_updated_data", self.entity_id)
        await self.coordinator.async_set_updated_data()

    async def _async_unset_mode_man(self):
        """
        Pomocná metoda pro vypnutí manuálního režimu nastavení teploty.
        """
        self._attr_supported_features = WaterHeaterEntityFeature.OPERATION_MODE
        _LOGGER.debug("%s : volani async_set_temperature", self.entity_id)
        await self.async_set_temperature(**{ATTR_TEMPERATURE: 0})
