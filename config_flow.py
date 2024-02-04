from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
import ipaddress

from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .heat_pump import HeatPump

_LOGGER = logging.getLogger(__name__)

# Schéma, které se používá pro zobrazení UI uživateli. Toto jednoduché
# schéma má jediné povinné pole pro IP adresu, ale může obsahovat více polí
# jako uživatelské jméno, heslo atd. Další příklady naleznete v komponentách HA.
# Vstup zobrazený uživateli bude přeložen. Viz soubory překladů a dokumentace:
DATA_SCHEMA = vol.Schema({("ip_address"): str})


async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    """
    Ověří uživatelský vstup, který nám umožní navázat spojení.

    Data obsahují klíče ze schématu DATA_SCHEMA s hodnotami poskytnutými uživatelem.
    """
    # Ověření, že data lze použít pro nastavení spojení.
    try:
        ipaddress.ip_address(data["ip_address"])
    except ValueError:
        # Pokud vstup není platná IP adresa, vyvolá výjimku
        raise InvalidAddress


    hp = HeatPump(hass, data["ip_address"])
    # Heat Pump poskytuje metodu `async_get_availability` pro ověření funkčnosti
    result = await hp.async_get_availability()
    if not result:
        # Pokud dojde k chybě, vyvolá výjimku
        raise CannotConnect

    # Vrací informace, které chcete uložit v konfiguračním záznamu.
    return {"title": "MasterTherm"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Zpracování konfiguračního toku pro MasterTherm."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input=None):
        """Zpracuje úvodní krok."""
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)

                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAddress:
                errors["ip_address"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # Pokud nejsou žádné uživatelské vstupy nebo byly nalezeny chyby, znovu zobrazí formulář, včetně nalezených chyb.
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Chyba indikující, že nelze navázat spojení."""


class InvalidAddress(exceptions.HomeAssistantError):
    """Chyba indikující neplatnou IP adresu."""
