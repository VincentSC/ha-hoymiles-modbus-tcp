import logging
from datetime import datetime, timedelta
from homeassistant.components.number import NumberEntity
from homeassistant.const import CONF_SCAN_INTERVAL
# from .hoymiles_dtu_client import HoymilesDtuClient
from .ha_hoymiles_dtu import HAHoymilesDTU

_LOGGER = logging.getLogger(__name__)
DOMAIN = "hoymiles_modbus_tcp"

# Define the throttling interval (5 minutes)
UPDATE_INTERVAL = timedelta(seconds=30)

SCAN_INTERVAL = timedelta(seconds=30)

async def async_setup_entry(hass, config_entry, async_add_entities):
    # client = hass.data[DOMAIN][config_entry.entry_id]
    dtu = HAHoymilesDTU(hass, DOMAIN, hass.data[DOMAIN][config_entry.entry_id])
    
    await dtu.map_microinverters()
    await dtu.fetch_serial_number()

    device_info = dtu.device_info
    sid = dtu.sid
    name = dtu.name

    entities = [
        HoymilesDTULevel(hass.data[DOMAIN][config_entry.entry_id], name, sid, device_info)
    ]
    async_add_entities(entities)

class HoymilesDTULevel(NumberEntity):
    """Representation of a Hoymiles power level sensor."""
    def __init__(self, client, name, sid, device_info):
        _LOGGER.debug(f"[numbers] Creating HoymilesMicroInverterLevel entity for {name} with SID {sid}")
        self._client = client
        self._sid = sid
        self._attr_name = f"{name} Power Level (%)"
        self._attr_unique_id = f"{sid}_power_level"
        self._attr_min_value = 5
        self._attr_max_value = 100
        self._attr_step = 1
        self._attr_native_value = 100
        self._attr_device_info = device_info
        self._attr_icon = "mdi:power-socket-eu"

        self._attr_should_poll = True

        self._last_write = datetime.min
        self._write_interval = timedelta(seconds=30)
        self._pending_value = None


    async def async_set_native_value(self, value: float) -> None:
        """Set the power level value with throttling to prevent frequent changes."""
        now = datetime.now()
        
        # Check if we're within the throttling interval
        if now - self._last_write < self._write_interval:
            _LOGGER.warning(
                f"[numbers] Power level change throttled for {self._attr_name}. "
                f"Last change was {(now - self._last_write).total_seconds():.1f}s ago. "
                f"Minimum interval is {self._write_interval.total_seconds()}s"
            )
            # Store the pending value for potential future use
            self._pending_value = value
            return
        
        try:
            _LOGGER.debug(f"[numbers] Setting power level to {value}% for {self._attr_name}")
            
            # Call the client method to write the power level
            await self._client.write_power_level(0xC001, int(value))
            
            # Update the native value and timestamp
            self._attr_native_value = value
            self._last_write = now
            self._pending_value = None
            
            _LOGGER.info(f"[numbers] Successfully set power level to {value}% for {self._attr_name}")
            
        except Exception as e:
            _LOGGER.error(f"[numbers] Failed to set power level to {value}% for {self._attr_name}: {e}")
            raise