from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import ENERGY_KILO_WATT_HOUR, POWER_WATT
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    config = hass.data[DOMAIN][entry.entry_id]["config"]

    devices = coordinator.data.get("devices", [])
    device_stats = coordinator.data.get("device_stats", {})

    sensors = []
    for device in devices:
        device_id = str(device.get("id"))
        if device_id in config["consumption"]:
            sensors.append(ComwattDeviceSensor(coordinator, device, "consumption"))
        elif device_id in config["production_self"]:
            sensors.append(ComwattDeviceSensor(coordinator, device, "production_self"))
        elif device_id in config["production_export"]:
            sensors.append(ComwattDeviceSensor(coordinator, device, "production_export"))

    async_add_entities(sensors)


class ComwattDeviceSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, device, role):
        super().__init__(coordinator)
        self._device = device
        self._role = role

        name = device.get("name") or f"Comwatt {device.get('id')}"
        self._attr_name = f"{name}"
        self._attr_unique_id = f"comwatt_{device.get('id')}"

        if role == "consumption":
            self._attr_icon = "mdi:power-plug"
        elif role == "production_self":
            self._attr_icon = "mdi:solar-power"
        elif role == "production_export":
            self._attr_icon = "mdi:transmission-tower-export"

        # Energie si cumul (id=1), sinon puissance
        if device.get("measure_type_id") == 1:
            self._attr_native_unit_of_measurement = ENERGY_KILO_WATT_HOUR
            self._attr_device_class = "energy"
            self._attr_state_class = "total_increasing"  # important pour l'énergie dashboard
        else:
            self._attr_native_unit_of_measurement = POWER_WATT
            self._attr_device_class = "power"
            self._attr_state_class = "measurement"

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, f"comwatt_box")},
            name="Comwatt Indepbox",
            manufacturer="Comwatt",
            model="Indepbox",
        )

    @property
    def native_value(self):
        stats = self.coordinator.data.get("device_stats", {})
        device_id = str(self._device.get("id"))
        return stats.get(device_id)

    @property
    def extra_state_attributes(self):
        return {
            "device_id": self._device.get("id"),
            "serial_number": self._device.get("serialNumber"),
            "ref": self._device.get("@ref"),
            "type": self._device.get("type", {}).get("label"),
            "partKind": self._device.get("partKind", {}).get("@ref"),
            "role": self._role
        }
