import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .hoymiles_dtu_client import HoymilesDtuClient

DOMAIN = "hoymiles_modbus_tcp"

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({
    vol.Required("dtu_ip"): str,
    vol.Required("dtu_port", default="502"): str,
})

class HoymilesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def _test_connection(self, dtu_ip: str, dtu_port: str) -> bool:
        """Test connection to DTU and return True if successful."""
        try:
            client = HoymilesDtuClient(host=dtu_ip, port=int(dtu_port))
            _LOGGER.debug(f"Testing connection to DTU at {dtu_ip}:{dtu_port}")
            await self.hass.async_add_executor_job(client.test_connection)
            await client.disconnect()
            return True
        except Exception as e:
            _LOGGER.error(f"Connection failed: {e}")
            return False

    def _create_data_schema(self, defaults: dict = None) -> vol.Schema:
        """Create data schema with optional default values."""
        defaults = defaults or {}
        return vol.Schema({
            vol.Required("dtu_ip", default=defaults.get("dtu_ip", "")): str,
            vol.Required("dtu_port", default=defaults.get("dtu_port", "502")): str,
        })

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            if await self._test_connection(user_input["dtu_ip"], user_input["dtu_port"]):
                return self.async_create_entry(title="Hoymiles Modbus TCP", data=user_input)
            else:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return HoymilesOptionsFlowHandler(config_entry)

class HoymilesOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def _test_connection(self, dtu_ip: str, dtu_port: str) -> bool:
        """Test connection to DTU and return True if successful."""
        try:
            _LOGGER.debug(f"Testing connection to DTU at {dtu_ip}:{dtu_port}")
            # Create a new client instance for testing
            client = HoymilesDtuClient(host=dtu_ip, port=dtu_port)
            _LOGGER.debug("Testing connection to Hoymiles DTU...")

            result = await client.test_connection()
            await client.disconnect()
            return result
        except Exception as e:
            _LOGGER.error(f"Connection failed: {e}")
            return False

    def _create_data_schema(self, defaults: dict = None) -> vol.Schema:
        """Create data schema with optional default values."""
        defaults = defaults or {}
        return vol.Schema({
            vol.Required("dtu_ip", default=defaults.get("dtu_ip", "")): str,
            vol.Required("dtu_port", default=defaults.get("dtu_port", "502")): str,
        })

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            if await self._test_connection(user_input["dtu_ip"], user_input["dtu_port"]):
                # Save the updated options
                self.hass.config_entries.async_update_entry(self.config_entry, data=user_input)
                return self.async_create_entry(title="", data={})
            else:
                return self.async_show_form(
                    step_id="init",
                    data_schema=self._create_data_schema(self.config_entry.data),
                    errors={"base": "cannot_connect"},
                )
        
        # Pre-fill the form with existing values
        return self.async_show_form(
            step_id="init",
            data_schema=self._create_data_schema(self.config_entry.data),
        )