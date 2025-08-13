
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .hoymiles_dtu_client import HoymilesDtuClient  # Import the client class


DOMAIN = "hoymiles_modbus_tcp"
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    _LOGGER.debug("Setting up Hoymiles Modbus config entry: %s", entry.data)

    client = HoymilesDtuClient(
        host=entry.data["dtu_ip"],
        port=entry.data["dtu_port"],
    )
    _LOGGER.debug("Connection to Hoymiles DTU established successfully.")
    
    hass.data[DOMAIN][entry.entry_id] = client
    _LOGGER.debug("Hoymiles Modbus TCP config entry setup complete: %s", entry.data)  
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "number"])

    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    await hass.config_entries.async_forward_entry_unload(entry, "number")
    # Clean up the client instance
    hass.data[DOMAIN].pop(entry.entry_id)
    return True

