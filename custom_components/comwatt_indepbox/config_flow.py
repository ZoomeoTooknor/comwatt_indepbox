import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN
from .client import ComwattClient

@config_entries.HANDLERS.register(DOMAIN)
class ComwattConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._errors = {}

    async def async_step_user(self, user_input=None):
        self._errors = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            try:
                client = ComwattClient(username, password)
                await client.authenticate()
            except Exception:
                self._errors["base"] = "invalid_auth"
            else:
                return self.async_create_entry(title="Comwatt Indepbox", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
            }),
            errors=self._errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry
        self.device_options = {}

    async def async_step_init(self, user_input=None):
        hass = self.hass
        username = self.config_entry.data[CONF_USERNAME]
        password = self.config_entry.data[CONF_PASSWORD]

        try:
            client = ComwattClient(username, password)
            await client.authenticate()
            devices = await client.get_devices()
            self.device_options = {
                str(device["id"]): device["name"]
                for device in devices if "name" in device
            }
        except Exception:
            return self.async_abort(reason="cannot_connect")

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional("consumption", default=self.config_entry.options.get("consumption", [])): cv.multi_select(self.device_options),
                vol.Optional("production_autoconsommation", default=self.config_entry.options.get("production_autoconsommation", [])): cv.multi_select(self.device_options),
                vol.Optional("production_revente", default=self.config_entry.options.get("production_revente", [])): cv.multi_select(self.device_options),
            })
        )