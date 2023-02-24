"""Platform for sensor integration."""
from __future__ import annotations
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .espsimple import (
    ESPSimpleSensor,
    ESPSimpleDevice,
    ESPSimpleDeviceRegistry,
    ESPSimpleSensorInfo,
)
from .persistent_storage import ESPSimpleStorage
from homeassistant.helpers import entity_platform as ep


def add_sensor(sensor: ESPSimpleSensor, async_add_entities: AddEntitiesCallback):
    async_add_entities([sensor])


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up esphome device based on a config entry."""

    entity_platform = ep.async_get_current_platform()

    device = ESPSimpleDevice(
        entry.data["device_id"],
        entry.title,
        entry.data["model"],
        entry.data["sw_version"],
        entity_platform,
    )

    ESPSimpleDeviceRegistry.add_device(device)

    device_storage = ESPSimpleStorage.get_device(device.device_id)

    sensor_list = list()

    for sensor_storage in device_storage["sensors"]:
        sensor = ESPSimpleSensor(
            hass,
            ESPSimpleSensorInfo(
                sensor_storage["name"],
                sensor_storage["unique_id"],
                device,
                sensor_storage["unit_of_measurement"],
                sensor_storage["device_class"],
                sensor_storage["state_class"],
            ),
        )
        sensor.set_state(sensor_storage["last_state"], False)
        device.add_sensor(sensor, False)
        sensor_list.append(sensor)

    async_add_entities(sensor_list)
