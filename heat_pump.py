from __future__ import annotations

from datetime import datetime
import asyncio, os, requests
from bs4 import BeautifulSoup
from functools import partial

from homeassistant.core import HomeAssistant

from .const import (
    MONITOR,
    REGULATOR,
)

import logging

_LOGGER = logging.getLogger(__name__)


class HeatPump:
    """
    Reprezentace tepelného čerpadla MasterTherm.

    Tato třída slouží jako základní interface pro komunikaci s tepelným čerpadlem.
    Umožňuje získávání dostupnosti čerpadla, stejně jako asynchronní načítání dat
    z jednotlivých zařízení spojených s čerpadlem.
    """

    manufacturer = "MasterTherm s.r.o."

    def __init__(self, hass: HomeAssistant, ip_address: str) -> None:
        """
        Inicializuje tepelné čerpadlo.

        Args:
            hass: Instance HomeAssistant, která poskytuje kontext a metody pro interakci s HA.
            ip_address: IP adresa tepelného čerpadla.
        """
        self._ip = ip_address
        self._hass = hass
        self._name = "MasterTherm"
        self._id = self._name.lower()
        self.online = None
        self._firmware = "0.1.1"
        self.devices = {
            MONITOR: Monitor(self._ip, self, self._firmware, self._hass),
            REGULATOR: Regulator(self._ip, self, self._firmware, self._hass),
        }

    @property
    def heatpump_id(self) -> str:
        """Vrátí ID tepelného čerpadla."""
        return self._id

    async def async_get_availability(self) -> bool:
        """
        Asynchronně ověří dostupnost tepelného čerpadla pomocí ping.

        Returns:
            bool: True, pokud je tepelné čerpadlo online, jinak False.
        """
        result = os.system("ping -c 2 " + self._ip)

        self.online = result == 0
        return self.online

    async def async_fetch_all_data(self):
        """
        Asynchronně načte všechna data z tepelného čerpadla.

        Načítá data z monitoru a regulátoru spojených s čerpadlem.
        """
        _LOGGER.debug("%s : volani monitor.async_fetch_all_data", self._name)
        await self.devices[MONITOR].async_fetch_data()

        _LOGGER.debug("%s : volani regulator.async_fetch_all_data", self._name)
        await self.devices[REGULATOR].async_fetch_data()


class Monitor:
    """
    Třída pro monitorování a získávání dat z tepelného čerpadla MasterTherm.
    
    Poskytuje metody pro asynchronní načítání dat z čerpadla a jeho komponent,
    jako jsou topné okruhy, a uchovává informace o stavu a měřeních.
    """

    def __init__(
        self,
        ip_address: str,
        hp: HeatPump,
        fw: str,
        hass: HomeAssistant,
        id="monitor",
        name="Monitor",
    ) -> None:
        """
        Inicializace monitoru.
        
        Args:
            ip_address: IP adresa tepelného čerpadla.
            hp: Instance tepelného čerpadla, ke kterému monitor patří.
            fw: Verze firmware tepelného čerpadla.
            hass: Instance HomeAssistant pro integraci s HA.
            id: Identifikátor monitoru.
            name: Lidsky čitelný název monitoru.
        """
        self.id = id
        self.hp = hp
        self.name = name
        self._ip = ip_address

        self._last_update = datetime.now()
        self.firmware_version = fw
        self._hass = hass
        self.model = "Monitor Device"
        self.online = None

        self._attributes = {
            "teplota_topne_vody": None,
            "venkovni_teplota": None,
            "zadana_teplota_topne_vody": None,
            "rychle_nastaveni_topne_vody": None,
            "rezim_zima": None,
            "rezim_leto": None,
            "kompresor": None,
            "obehove_cerpadlo": None,
            "ventilator": None,
            "elektrokotel_1": None,
            "elektrokotel_2": None,
            "podminka_odtaveni": None,
            "alarm": None,
            "kod_alarmu": None,
            "3_alarmy": None,
            "reset_3_alarmu": None,
            "odtaveni": None,
            "cas_od_odtaveni": None,
            "zapnuto": None,
            "venku_bod_a": None,
            "topna_voda_bod_a": None,
            "venku_bod_b": None,
            "topna_voda_bod_b": None,
            "teplota_povoleni_elektrokotle": None,
            "hodiny_kompresoru": None,
            "starty_kompresoru": None,
            "hodiny_cerpadla": None,
            "pocet_chyb_ventilatoru": None,
            "pocet_chyb_kompresoru": None,
            "pocet_chyb_protimrazu": None,
            "topne_okruhy": {
                "to1": self.TopnyOkruh("TO1"),
                "to3": self.TopnyOkruh("TO3"),
            },
        }

    class TopnyOkruh:
        """Třída reprezentující topný okruh v systému monitorování."""

        def __init__(self, name: str):
            """
            Inicializace topného okruhu.
            
            Args:
                name: Název topného okruhu.
            """
            self._attributes = {
                "name": name,
                # Zde jsou definovány další atributy topného okruhu
                "skutecna_teplota": None,
                "zadana_teplota": None,
                "venku_bod_a": None,
                "topna_voda_bod_a": None,
                "venku_bod_b": None,
                "topna_voda_bod_b": None,
                "hystereze": None,
                "rychle_nastaveni_teploty": None,
                "analogovy_vystup": None,
                "digitalni_vystup": None,
            }

    @property
    def monitor_id(self) -> str:
        """Vrátí identifikátor monitoru."""
        return self._id

    def get_availability(self):
        """
        Zjistí dostupnost monitoru založenou na dostupnosti tepelného čerpadla.
        
        Returns:
            bool: True, pokud je monitor dostupný, jinak False.
        """
        self.online = self.hp.online
        return self.online

    def get_state(self, key):
        """
        Vrátí stav nebo hodnotu konkrétního atributu monitoru nebo topného okruhu.
        
        Args:
            key: Klíč atributu.
        
        Returns:
            Hodnota požadovaného atributu.
        """
        if key[:3] in ["to1", "to3"]:
            return self._attributes["topne_okruhy"][key[:3]]._attributes[key[4:]]
        return self._attributes[key]

    async def async_fetch_data(self):
        """
        Asynchronně načte všechna dostupná data z tepelného čerpadla.
        
        Tato metoda získává data pomocí HTTP požadavku na IP adresu tepelného čerpadla,
        analyzuje odpověď a aktualizuje interní stav monitoru a topných okruhů.
        """

        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "cs-CZ,cs;q=0.9",
            "Authorization": "Basic bWFzdGVydGhlcm06Zm1hc3RlcnRoZXJt",
            "Connection": "keep-alive",
            "Referer": "http://" + self._ip + "/http/index.html",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

        params = ""

        partial_request = partial(
            requests.get,
            "http://" + self._ip + "/http/index.html",
            params=params,
            headers=headers,
            verify=False,
        )

        response = await self._hass.async_add_executor_job(partial_request)
        parsovany_text = BeautifulSoup(response.text, "html.parser")
        vyhledano_tr = parsovany_text.find_all("tr")

        self._attributes["teplota_topne_vody"] = float(vyhledano_tr[1].td.string)
        self._attributes["venkovni_teplota"] = float(vyhledano_tr[2].td.string)
        self._attributes["zadana_teplota_topne_vody"] = float(vyhledano_tr[5].td.string)
        self._attributes["rychle_nastaveni_topne_vody"] = float(
            vyhledano_tr[6].td.string
        )
        self._attributes["nastaveni_eev"] = float(vyhledano_tr[7].td.string)
        self._attributes["rezim_zima"] = int(vyhledano_tr[8].td.string)
        self._attributes["rezim_leto"] = self._invert_binary_sensor(
            int(vyhledano_tr[8].td.string)
        )

        self._attributes["kompresor"] = int(vyhledano_tr[12].td.string)
        self._attributes["obehove_cerpadlo"] = int(vyhledano_tr[13].td.string)
        self._attributes["ventilator"] = int(vyhledano_tr[15].td.string)
        self._attributes["elektrokotel_1"] = int(vyhledano_tr[16].td.string)
        self._attributes["elektrokotel_2"] = int(vyhledano_tr[17].td.string)
        self._attributes["podminka_odtaveni"] = int(vyhledano_tr[24].td.string)
        self._attributes["alarm"] = int(vyhledano_tr[25].td.string)
        self._attributes["kod_alarmu"] = int(vyhledano_tr[26].td.string)
        self._attributes["3_alarmy"] = int(vyhledano_tr[27].td.string)
        self._attributes["reset_3_alarmu"] = int(vyhledano_tr[28].td.string)
        self._attributes["odtaveni"] = int(vyhledano_tr[30].td.string)
        self._attributes["cas_od_odtaveni"] = int(vyhledano_tr[31].td.string)
        self._attributes["zapnuto"] = int(vyhledano_tr[33].td.string)

        self._attributes["venku_bod_a"] = float(vyhledano_tr[36].td.string)
        self._attributes["topna_voda_bod_a"] = float(vyhledano_tr[37].td.string)
        self._attributes["venku_bod_b"] = float(vyhledano_tr[38].td.string)
        self._attributes["topna_voda_bod_b"] = float(vyhledano_tr[39].td.string)
        self._attributes["teplota_povoleni_elektrokotle"] = float(
            vyhledano_tr[40].td.string
        )

        self._attributes["hodiny_kompresoru"] = int(vyhledano_tr[42].td.string)
        self._attributes["starty_kompresoru"] = int(vyhledano_tr[43].td.string)
        self._attributes["hodiny_cerpadla"] = int(vyhledano_tr[44].td.string)
        self._attributes["pocet_chyb_ventilatoru"] = int(vyhledano_tr[51].td.string)
        self._attributes["pocet_chyb_kompresoru"] = int(vyhledano_tr[52].td.string)
        self._attributes["pocet_chyb_protimrazu"] = int(vyhledano_tr[53].td.string)

        self._attributes["topne_okruhy"]["to1"]._attributes["skutecna_teplota"] = float(
            vyhledano_tr[55].td.string
        )
        self._attributes["topne_okruhy"]["to1"]._attributes["zadana_teplota"] = float(
            vyhledano_tr[56].td.string
        )
        self._attributes["topne_okruhy"]["to1"]._attributes["venku_bod_a"] = float(
            vyhledano_tr[57].td.string
        )
        self._attributes["topne_okruhy"]["to1"]._attributes["topna_voda_bod_a"] = float(
            vyhledano_tr[58].td.string
        )
        self._attributes["topne_okruhy"]["to1"]._attributes["venku_bod_b"] = float(
            vyhledano_tr[59].td.string
        )
        self._attributes["topne_okruhy"]["to1"]._attributes["topna_voda_bod_b"] = float(
            vyhledano_tr[60].td.string
        )
        self._attributes["topne_okruhy"]["to1"]._attributes["hystereze"] = float(
            vyhledano_tr[61].td.string
        )
        self._attributes["topne_okruhy"]["to1"]._attributes[
            "rychle_nastaveni_teploty"
        ] = float(vyhledano_tr[62].td.string)
        self._attributes["topne_okruhy"]["to1"]._attributes["analogovy_vystup"] = float(
            vyhledano_tr[63].td.string
        )
        self._attributes["topne_okruhy"]["to1"]._attributes["digitalni_vystup"] = int(
            vyhledano_tr[64].td.string
        )

        self._attributes["topne_okruhy"]["to3"]._attributes["skutecna_teplota"] = float(
            vyhledano_tr[77].td.string
        )
        self._attributes["topne_okruhy"]["to3"]._attributes["zadana_teplota"] = float(
            vyhledano_tr[78].td.string
        )
        self._attributes["topne_okruhy"]["to3"]._attributes["venku_bod_a"] = float(
            vyhledano_tr[79].td.string
        )
        self._attributes["topne_okruhy"]["to3"]._attributes["topna_voda_bod_a"] = float(
            vyhledano_tr[80].td.string
        )
        self._attributes["topne_okruhy"]["to3"]._attributes["venku_bod_b"] = float(
            vyhledano_tr[81].td.string
        )
        self._attributes["topne_okruhy"]["to3"]._attributes["topna_voda_bod_b"] = float(
            vyhledano_tr[82].td.string
        )
        self._attributes["topne_okruhy"]["to3"]._attributes["hystereze"] = float(
            vyhledano_tr[83].td.string
        )
        self._attributes["topne_okruhy"]["to3"]._attributes[
            "rychle_nastaveni_teploty"
        ] = float(vyhledano_tr[84].td.string)
        self._attributes["topne_okruhy"]["to3"]._attributes["digitalni_vystup"] = int(
            vyhledano_tr[85].td.string
        )

        self._last_update = datetime.now()

    def _invert_binary_sensor(self, value) -> int:
        if value == 1:
            return 0
        return 1


##################################################################################


class Regulator:
    """
    Třída pro regulování a získávání dat z tepelného čerpadla MasterTherm.
    
    Poskytuje metody pro asynchronní načítání a nahrávání dat z čerpadla a jeho komponent,
    jako jsou topné okruhy, a uchovává informace o stavu a měřeních.
    """
    def __init__(
        self,
        ip_address: str,
        hp: HeatPump,
        fw: str,
        hass: HomeAssistant,
        id="regulator",
        name="Regulator",
    ) -> None:
        """
        Inicializace regulátoru.
        
        Args:
            ip_address: IP adresa tepelného čerpadla.
            hp: Instance tepelného čerpadla, ke kterému monitor patří.
            fw: Verze firmware tepelného čerpadla.
            hass: Instance HomeAssistant pro integraci s HA.
            id: Identifikátor monitoru.
            name: Lidsky čitelný název monitoru.
        """
        self.id = id
        self.hp = hp
        self.name = name
        self._ip = ip_address

        self._last_update = datetime.now()
        self.firmware_version = fw
        self._hass = hass
        self.model = "Regulator Device"
        self.online = None

        
        self._attributes = {
            "restart_alarmu": None,
            "zapnuto": None,
            "teplota_prepnuti_leto": None,
            "teplota_prepnuti_zima": None,
            "rezim_zima_leto": None,
            "rychle_nastaveni_topne_vody": None,
            "venku_bod_a": None,
            "topna_voda_bod_a": None,
            "venku_bod_b": None,
            "topna_voda_bod_b": None,
            "teplota_povoleni_elektrokotle": None,
            "topne_okruhy": {
                "to1": self.TopnyOkruh("TO1"),
                "to3": self.TopnyOkruh("TO3"),
            },
        }

    class TopnyOkruh:
        """Třída reprezentující topný okruh v systému regulování."""

        def __init__(self, name: str):
            """
            Inicializace topného okruhu.
            
            Args:
                name: Název topného okruhu.
            """
            self._attributes = {
                "name": name,
                
                "program_okruhu": None,
                "venku_bod_a": None,
                "topna_voda_bod_a": None,
                "venku_bod_b": None,
                "topna_voda_bod_b": None,
                "rychle_nastaveni_teploty": None,
            }

    @property
    def regulator_id(self) -> str:
        """Vrátí identifikátor regulátoru."""
        return self._id

    def get_availability(self):
        """
        Zjistí dostupnost regulátoru založenou na dostupnosti tepelného čerpadla.
        
        Returns:
            bool: True, pokud je monitor dostupný, jinak False.
        """
        self.online = self.hp.online
        return self.online

    def get_state(self, key):
        """
        Vrátí stav nebo hodnotu konkrétního atributu regulátoru nebo topného okruhu.
        
        Args:
            key: Klíč atributu.
        
        Returns:
            Hodnota požadovaného atributu.
        """
        if key[:3] in ["to1", "to3"]:
            return self._attributes["topne_okruhy"][key[:3]]._attributes[key[4:]]
        return self._attributes[key]

    async def async_fetch_data(self):
        """
        Asynchronně načte všechna dostupná data z tepelného čerpadla.
        
        Tato metoda získává data pomocí HTTP požadavku na IP adresu tepelného čerpadla,
        analyzuje odpověď a aktualizuje interní stav regulátoru a topných okruhů.
        """

        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "cs-CZ,cs;q=0.9",
            "Authorization": "Basic bWFzdGVydGhlcm06Zm1hc3RlcnRoZXJt",
            "Connection": "keep-alive",
            "Referer": "http://" + self._ip + "/http/index.html",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

        params = ""

        partial_request = partial(
            requests.get,
            "http://" + self._ip + "/http/edit.html",
            params=params,
            headers=headers,
            verify=False,
        )

        response = await self._hass.async_add_executor_job(partial_request)
        parsovany_text = BeautifulSoup(response.text, "html.parser")
        vyhledano_tr = parsovany_text.find_all("tr")

        self._attributes["restart_3_alarmu"] = int(self._find_value(vyhledano_tr[1].td))
        self._attributes["zapnuto"] = int(self._find_value(vyhledano_tr[2].td))
        self._attributes["teplota_prepnuti_leto"] = float(
            self._find_value(vyhledano_tr[3].td)
        )
        self._attributes["teplota_prepnuti_zima"] = float(
            self._find_value(vyhledano_tr[4].td)
        )
        self._attributes["rezim_zima_leto"] = int(self._find_value(vyhledano_tr[5].td))
        self._attributes["rychle_nastaveni_topne_vody"] = float(
            self._find_value(vyhledano_tr[7].td)
        )

        self._attributes["venku_bod_a"] = float(self._find_value(vyhledano_tr[8].td))
        self._attributes["topna_voda_bod_a"] = float(
            self._find_value(vyhledano_tr[9].td)
        )
        self._attributes["venku_bod_b"] = float(self._find_value(vyhledano_tr[10].td))
        self._attributes["topna_voda_bod_b"] = float(
            self._find_value(vyhledano_tr[11].td)
        )
        self._attributes["teplota_povoleni_elektrokotle"] = float(
            self._find_value(vyhledano_tr[12].td)
        )

        self._attributes["topne_okruhy"]["to1"]._attributes["program_okruhu"] = int(
            self._find_value(vyhledano_tr[19].td)
        )
        self._attributes["topne_okruhy"]["to1"]._attributes["venku_bod_a"] = float(
            self._find_value(vyhledano_tr[20].td)
        )
        self._attributes["topne_okruhy"]["to1"]._attributes["topna_voda_bod_a"] = float(
            self._find_value(vyhledano_tr[21].td)
        )
        self._attributes["topne_okruhy"]["to1"]._attributes["venku_bod_b"] = float(
            self._find_value(vyhledano_tr[22].td)
        )
        self._attributes["topne_okruhy"]["to1"]._attributes["topna_voda_bod_b"] = float(
            self._find_value(vyhledano_tr[23].td)
        )
        self._attributes["topne_okruhy"]["to1"]._attributes[
            "rychle_nastaveni_teploty"
        ] = float(self._find_value(vyhledano_tr[24].td))

        self._attributes["topne_okruhy"]["to3"]._attributes["program_okruhu"] = int(
            self._find_value(vyhledano_tr[33].td)
        )
        self._attributes["topne_okruhy"]["to3"]._attributes["venku_bod_a"] = float(
            self._find_value(vyhledano_tr[34].td)
        )
        self._attributes["topne_okruhy"]["to3"]._attributes["topna_voda_bod_a"] = float(
            self._find_value(vyhledano_tr[35].td)
        )
        self._attributes["topne_okruhy"]["to3"]._attributes["venku_bod_b"] = float(
            self._find_value(vyhledano_tr[36].td)
        )
        self._attributes["topne_okruhy"]["to3"]._attributes["topna_voda_bod_b"] = float(
            self._find_value(vyhledano_tr[37].td)
        )
        self._attributes["topne_okruhy"]["to3"]._attributes[
            "rychle_nastaveni_teploty"
        ] = float(self._find_value(vyhledano_tr[38].td))

        self._last_update = datetime.now()

    def _find_value(self, text):
        """
        Asynchronně odesílá data do tepelného čerpadla.

        Tato metoda používá HTTP GET požadavek k odeslání dat na určitý klíč a hodnotu
        do tepelného čerpadla. Slouží pro nastavení konfigurace nebo ovládacích
        parametrů čerpadla.

        Args:
            key: Klíč, pod kterým se mají data uložit.
            value: Hodnota, která se má pro daný klíč nastavit.
        """
        text = str(text)
        value_start = text.index("value=") + 7
        value_stop = text.index("/></td>") - 1

        return text[value_start:value_stop]

    async def async_upload_data(self, key, value):
        """
        Asynchronně odesílá data do tepelného čerpadla.

        Tato metoda používá HTTP GET požadavek k odeslání dat na určitý klíč a hodnotu
        do tepelného čerpadla. Slouží pro nastavení konfigurace nebo ovládacích
        parametrů čerpadla.

        Args:
            key: Klíč, pod kterým se mají data uložit.
            value: Hodnota, která se má pro daný klíč nastavit.
        """
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "cs-CZ,cs;q=0.9",
            "Authorization": "Basic bWFzdGVydGhlcm06Zm1hc3RlcnRoZXJt",
            "Connection": "keep-alive",
            "Referer": "http://" + self._ip + "/http/edit.html?",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

        params = {
            "?script:var" + key: str(value),
        }

        # Vytvoření částečného HTTP požadavku s použitím funkce `partial`.
        partial_request = partial(
            requests.get,
            "http://" + self._ip + "/http/edit.html",
            params=params,
            headers=headers,
            verify=False,
        )

        await self._hass.async_add_executor_job(partial_request)
