import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD
from .client import ComwattClient

@config_entries.HANDLERS.register(DOMAIN)
class ComwattConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gère le flux de configuration pour Comwatt Indepbox."""

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
                self.sites = await client.get_sites()
                self.devices = []
                for site in self.sites:
                    self.devices.extend(await client.get_devices(site["id"]))

                # Sauvegarde temporaire dans context
                self.context_data = {
                    "username": username,
                    "password": password,
                    "devices": self.devices
                }

                return await self.async_step_device_selection()
            except Exception:
                self._errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): cv.string,
                    vol.Required(CONF_PASSWORD): cv.string,
                }
            ),
            errors=self._errors,
        )

    async def async_step_device_selection(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="Comwatt Indepbox",
                data={
                    CONF_USERNAME: self.context_data["username"],
                    CONF_PASSWORD: self.context_data["password"],
                    "production_autoconso": user_input["production_autoconso"],
                    "production_revente": user_input["production_revente"],
                    "consommation": user_input["consommation"]
                }
            )

        device_names = {str(d["id"]): d["name"] for d in self.context_data["devices"]}

        return self.async_show_form(
            step_id="device_selection",
            data_schema=vol.Schema({
                vol.Required("production_autoconso"): vol.In(device_names),
                vol.Required("production_revente"): vol.In(device_names),
                vol.Required("consommation"): vol.In(device_names),
            }),
            description_placeholders=device_names
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry
        self.client = ComwattClient(
            config_entry.data[CONF_USERNAME],
            config_entry.data[CONF_PASSWORD]
        )
        self.devices = []

    async def async_step_init(self, user_input=None):
        # Authentifie et récupère les devices si ce n’est pas déjà fait
        await self.client.authenticate()
        self.devices = await self.client.get_devices()

        # Construit une map id → nom
        device_choices = {str(d["id"]): d["name"] for d in self.devices}

        options = self.config_entry.options
        default_consumption = options.get("consumption", [])
        default_self = options.get("production_autoconsommation", [])
        default_export = options.get("production_revente", [])

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional("consumption", default=default_consumption): cv.multi_select(device_choices),
                vol.Optional("production_autoconsommation", default=default_self): cv.multi_select(device_choices),
                vol.Optional("production_revente", default=default_export): cv.multi_select(device_choices),
            }),
        )

    async def async_step_user(self, user_input=None):
        return self.async_create_entry(title="", data=user_input)