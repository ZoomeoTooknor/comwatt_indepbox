from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import POWER_WATT

from .const import DOMAIN, DEFAULT_ICON


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    devices = coordinator.data.get("devices", [])
    sensors = []

    for device in devices:
        if "id" in device and "name" in device:
            sensors.append(ComwattDeviceSensor(coordinator, device))

    async_add_entities(sensors)


class ComwattDeviceSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, device):
        super().__init__(coordinator)
        self._device = device
        self._attr_name = f"{device.get('name')}"
        self._attr_unique_id = f"comwatt_{device.get('id')}"
        self._attr_icon = DEFAULT_ICON
        self._attr_native_unit_of_measurement = POWER_WATT
        self._attr_device_class = "power"

    @property
    def native_value(self):
        stats = self.coordinator.data.get("device_stats", {})
        device_id = str(self._device.get("id"))
        return stats.get(device_id)