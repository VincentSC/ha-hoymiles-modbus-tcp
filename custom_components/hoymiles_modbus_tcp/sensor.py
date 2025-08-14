# custom_components/hoymiles_modbus_tcp/sensor.py

import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfPower, UnitOfEnergy  # Updated imports for units
import time


# from .hoymiles_dtu_client import HoymilesClient
from .ha_hoymiles_dtu import HAHoymilesDTU


_LOGGER = logging.getLogger(__name__)
DOMAIN = "hoymiles_modbus_tcp"


async def async_setup_entry(hass, config_entry, async_add_entities):
    dtu = HAHoymilesDTU(hass, DOMAIN, hass.data[DOMAIN][config_entry.entry_id])

    await dtu.map_microinverters()
    await dtu.fetch_serial_number()
    

    device_info = dtu.device_info
    sid = dtu.sid
    name = dtu.name
    _LOGGER.debug(f"Setting up Hoymiles DTU with SID {sid} and name {name}")

    entities = [
        HoymilesStationPowerSensor(hass.data[DOMAIN][config_entry.entry_id], name, sid, device_info),
        HoymilesStationDailyEnergySensor(hass.data[DOMAIN][config_entry.entry_id], name, sid, device_info)
    ]
    async_add_entities(entities)



class HoymilesStationPowerSensor(SensorEntity):
    def __init__(self, client, name, sid, device_info):
        self._client = client
        self._sid = sid
        self._attr_name = f"{name} Current Power"
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_unique_id = f"{sid}_power"
        self._attr_device_class = "power"
        self._attr_state_class = "measurement"
        self._attr_icon = "mdi:solar-power"
        self._attr_native_value = None  # Initial value, will be updated in async_update
        self._attr_should_poll = True
        self._attr_device_info = device_info
        self._state = None
        self_last_update = time.time()

    @property
    def native_value(self):
        return self._state
    
    @property
    def scan_interval(self):
        """Return the scan interval in seconds."""
        return 120


    async def async_update(self):
        _LOGGER.debug(f"Fetching current power for station {self._sid}")
        power = await self._client.get_total_power()
        _LOGGER.debug(f"Received power data for station {self._sid}: {power/1000} kW")
        self._state = float(power)


class HoymilesStationDailyEnergySensor(SensorEntity):
    def __init__(self, client, name, sid, device_info):
        self._client = client
        self._sid = sid
        self._attr_name = f"{name} Daily Energy"
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_unique_id = f"{sid}_daily_energy"
        self._attr_device_class = "energy"
        self._attr_state_class = "total_increasing"
        self._attr_icon = "mdi:solar-power"
        self._attr_native_value = None
        self._attr_should_poll = True
        self._attr_device_info = device_info
        self._state = None

    @property
    def native_value(self):
        return self._state

    @property
    def scan_interval(self):
        """Return the scan interval in seconds."""
        return 120

    async def async_update(self):
        #only update the daily energy once every 2 minutes
        if self._state is not None and (time.time() - self._last_update < 120):
            _LOGGER.debug(f"Skipping update for station {self._sid}, last update was too recent.")
            return
        self._last_update = time.time()


        _LOGGER.debug(f"Fetching daily energy for station {self._sid}")
        daily_energy = await self._client.get_daily_power()
        _LOGGER.debug(f"Received daily energy data for station {self._sid}: {daily_energy} kWh")
        self._state = float(daily_energy)/1000
        # Convert to kWh