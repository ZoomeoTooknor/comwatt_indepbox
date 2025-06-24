from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL, CONF_USERNAME, CONF_PASSWORD, PLATFORMS
from .client import ComwattClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Configure une entrée de l'intégration Comwatt Indepbox."""
    hass.data.setdefault(DOMAIN, {})

    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    client = ComwattClient(username, password)

    async def async_update_data():
        """Fonction appelée à chaque rafraîchissement."""
        try:
            await client.authenticate()
            user = await client.get_authenticated_user()
            indepboxes = await client.get_indepboxes(user["id"])
            devices = await client.get_devices()
            device_ids = [device["id"] for device in devices]
            stats = await client.get_device_stats(device_ids)
            return {
                "devices": devices,
                "device_stats": stats
            }
        except Exception as err:
            raise UpdateFailed(f"Erreur lors de la récupération des données Comwatt: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="comwatt_indepbox",
        update_method=async_update_data,
        update_interval=timedelta(minutes=1),  # passage à la minute
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "client": client,
    }
    hass.data[DOMAIN][entry.entry_id]["config"] = {
        "consumption": entry.options.get("consumption", []),
        "production_self": entry.options.get("production_autoconsommation", []),
        "production_export": entry.options.get("production_revente", []),
    }

    if entry.options:
        hass.data[DOMAIN][entry.entry_id]["options"] = entry.options
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Nettoyage à la suppression de l'intégration."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok