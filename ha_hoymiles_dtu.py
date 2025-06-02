import logging
_LOGGER = logging.getLogger(__name__)

class HAHoymilesDTU:
    def __init__(self, hass, DOMAIN, client):
        self.serial = None
        self.DOMAIN = DOMAIN
        self.hass = hass
        self._client = client


    async def fetch_serial_number(self):
        self.serial = await self._client.read_serial_number()
        if not self.serial:
            raise ValueError("Failed to fetch serial number from Hoymiles DTU.")
        _LOGGER.debug(f"Serial number set to: {self.serial}")
        return self.serial
 
    async def map_microinverters(self):
        # _LOGGER.debug("Connecting to Hoymiles DTU...")
        # await self.hass.async_add_executor_job(self._client.connect)
        _LOGGER.debug("Mapping microinverters...")
        count = await self._client.map_microinverters()
        if count is None:
            raise ValueError("Failed to map microinverters. No microinverters found.")
        _LOGGER.debug(f"Mapped {count} microinverters.")
        return count

    @property
    def device_info(self):
        return {
            "identifiers": {(self.DOMAIN, self.sid)},
            "name": self.name,
            "manufacturer": "Hoymiles",
            "model": "PRO (s)",
        }

    @property
    def sid(self):
        if not self.serial:
            raise ValueError("Serial number not set. Call fetch_serial_number() first.")
        return f"hoymiles_dtu_{self.serial}_tcp"
    @property
    def name(self):
        if not self.serial:
            raise ValueError("Serial number not set. Call fetch_serial_number() first.")
        return f"Hoymiles DTU {self.serial}"

