from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator, UpdateFailed
)

from datetime import timedelta
import logging
_LOGGER = logging.getLogger(__name__)

from .heat_pump import HeatPump

class HeatPumpCoordinator(DataUpdateCoordinator):
    """Vlastní koordinátor pro aktualizaci dat."""

    def __init__(self, hass, hp: HeatPump, update_interval=timedelta(seconds=60)):
        """Inicializace koordinátoru."""
        _LOGGER.debug('inicializace HeatPumpCoordinator')
        
        super().__init__(
            hass,
            logger=_LOGGER,
            name="HeatPumpCoordinator",
            update_interval=update_interval,
        )
        self.hass = hass
        self.hp = hp

        _LOGGER.debug('update_interval: %s', self.update_interval)
        _LOGGER.debug('always_update: %s', self.always_update)


    async def _async_update_data(self):
        """Načtení dat z externího zdroje."""
        _LOGGER.debug('%s : volano _async_update_data', self.name)

        _LOGGER.debug('%s : volani Heat Pump async_get_availability', self.name)
        if await self.hp.async_get_availability():
            _LOGGER.debug('%s : Heat Pump je dostupny', self.name)
            try:
                _LOGGER.debug('%s : volani Heat Pump async_fetch_all_data', self.name)
                await self.hp.async_fetch_all_data()
                _LOGGER.debug('volani Heat Pump async_fetch_all_data probehlo uspesne')
            except Exception as e:
                _LOGGER.debug('volani Heat Pump async_fetch_all_data probehlo NEuspesne')
                raise UpdateFailed(f"Chyba při aktualizaci dat: {e}")
