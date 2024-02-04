# Integrace Vodního Tepelného Čerpadla

Tato integrace vám umožňuje ovládat a monitorovat vodní tepelné čerpadlo přímo z Home Assistant. Nabízí několik entit, které vám poskytují informace o aktuálním stavu a umožňují vám nastavit různé parametry čerpadla.

## Funkce

- **Monitorování teploty**: Získávejte aktuální teploty topné vody, venkovní teplotu, a další.
- **Nastavení teploty**: Můžete nastavit cílovou teplotu topné vody pro různé režimy provozu.
- **Režimy provozu**: Přepínejte mezi automatickým, letním, zimním a manuálním režimem provozu.
- **Monitorování provozu**: Zobrazujte dobu provozu kompresoru, čerpadla a další statistiky.

## Instalace

1. Zkopírujte složku integrace do svého adresáře `custom_components` ve vaší instalaci Home Assistant.
2. Restartujte Home Assistant.
3. Přejděte do `Nastavení` > `Integrace` a klikněte na `Přidat integraci`.
4. Vyhledejte `Vodní Tepelné Čerpadlo` a postupujte podle instrukcí pro dokončení nastavení.

## Konfigurace

Po přidání integrace budete vyzváni k zadání IP adresy vašeho tepelného čerpadla. Nastavení dále umožňuje specifikovat jednotlivé režimy provozu a teploty, které chcete monitorovat a ovládat.

## Podporované Entity

- `sensor`: Teploty a další monitorované hodnoty.
- `water_heater`: Entita pro nastavení a kontrolu režimu a teploty topení.
- `number`: Entita pro přesné nastavení teplot a jiných hodnot pomocí numerických vstupů.

## Vlastnosti

- **Operation Mode**: Umožňuje výběr z přednastavených režimů provozu.
- **Current Temperature**: Zobrazuje aktuální teplotu topné vody.
- **Target Temperature**: Umožňuje nastavit cílovou teplotu pro vybraný režim provozu.
