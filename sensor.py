"""Platform for sensor integration."""
from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.config_entries import ConfigEntry
from .sensor_handler import ESPSimpleSensorHandler


def add_sensor(sensor: ESPSimpleSensor, async_add_entities: AddEntitiesCallback):
    ESPSimpleSensorHandler.add_device(sensor)
    async_add_entities([sensor])


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up esphome sensors based on a config entry."""

    for sensor in entry.data["sensors"]:
        add_sensor(
            ESPSimpleSensor(
                hass,
                entry,
                ESPSimpleSensorInfo(
                    entry.title + " " + sensor["display_name"],
                    sensor["identifier"],
                    entry.data["device_id"],
                    "°C",
                    SensorDeviceClass.TEMPERATURE,
                    SensorStateClass.MEASUREMENT,
                ),
            ),
            async_add_entities,
        )


class ESPSimpleSensorInfo:
    def __init__(
        self,
        name: str,
        unique_id: str,
        device_id: str,
        unit_of_measurement: str,
        device_class: SensorDeviceClass,
        state_class: SensorStateClass,
    ) -> None:
        self.name: str = name
        self.unique_id: str = unique_id
        self.device_id: str = device_id
        self.unit_of_measurement: str = unit_of_measurement
        self.device_class: SensorDeviceClass = device_class
        self.state_class: SensorStateClass = state_class


class ESPSimpleSensor(SensorEntity):
    """Representation of a Sensor."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, info: ESPSimpleSensorInfo
    ) -> None:
        self.hass: HomeAssistant = hass
        self.entry: ConfigEntry = entry
        self.info: ESPSimpleSensorInfo = info
        self.state_value: str = ""

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        return self.state_value

    @property
    def state_class(self) -> SensorStateClass | str | None:
        return self.info.state_class

    @property
    def device_class(self) -> SensorDeviceClass | None:
        return self.info.device_class

    @property
    def native_unit_of_measurement(self) -> str | None:
        return self.info.unit_of_measurement

    @property
    def unique_id(self) -> str | None:
        return self.info.device_id + "_" + self.info.unique_id

    @property
    def name(self) -> str | None:
        return self.info.name

    def set_state(self, state):
        self.hass.states.set(self.entity_id, state)
        self.state_value = state
