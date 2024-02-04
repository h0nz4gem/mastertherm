from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from datetime import timedelta
import logging

_LOGGER = logging.getLogger(__name__)

from .heat_pump import HeatPump


class HeatPumpCoordinator(DataUpdateCoordinator):
    """
    Koordinátor pro aktualizaci dat tepelného čerpadla.
    
    Tato třída rozšiřuje DataUpdateCoordinator a zajišťuje pravidelné aktualizace dat
    z tepelného čerpadla. Používá async metody tepelného čerpadla pro získání a aktualizaci dat.
    """

    def __init__(self, hass, hp: HeatPump, update_interval=timedelta(minutes=2)):
        """Inicializuje HeatPumpCoordinator."""

        super().__init__(
            hass,
            logger=_LOGGER,
            name="HeatPumpCoordinator",
            update_interval=update_interval,
        )
        self.hass = hass
        self.hp = hp

    async def _async_update_data(self):
        """
        Asynchronně aktualizuje data tepelného čerpadla.
        
        Získává dostupnost tepelného čerpadla a pokud je dostupné, pokusí se získat všechna data.
        Pokud dojde k chybě, vyvolá výjimku UpdateFailed.
        """
        _LOGGER.debug("%s : volani Heat Pump async_get_availability", self.name)
        if await self.hp.async_get_availability():
            _LOGGER.debug("%s : Heat Pump je dostupny", self.name)
            try:
                _LOGGER.debug("%s : volani Heat Pump async_fetch_all_data", self.name)
                await self.hp.async_fetch_all_data()

            except Exception as e:
                _LOGGER.debug(
                    "volani Heat Pump async_fetch_all_data probehlo NEuspesne"
                )
                raise UpdateFailed(f"Chyba při aktualizaci dat: {e}")

    async def async_set_updated_data(self):
        """
        Nastaví aktualizovaná data pro tepelné čerpadlo.
        
        Zruší aktuálně naplánovanou aktualizaci, provede aktualizaci dat a pokud má posluchače,
        naplánuje novou aktualizaci. Informuje posluchače o aktualizaci.
        """
        # Zruší aktuálně naplánovanou aktualizaci.
        self._async_unsub_refresh()
        # Zruší odloženou aktualizaci.
        self._debounced_refresh.async_cancel()

        try:
            _LOGGER.debug("%s : volani Heat Pump async_fetch_all_data", self.name)
            await self.hp.async_fetch_all_data()
            self.last_update_success = True

            # Pokud existují posluchači, naplánuje novou aktualizaci.
            if self._listeners:
                self._schedule_refresh()

            # Informuje posluchače o aktualizaci.
            self.async_update_listeners()

        except Exception as e:
            _LOGGER.debug("volani Heat Pump async_fetch_all_data probehlo NEuspesne")
            raise UpdateFailed(f"Chyba při aktualizaci dat: {e}")
