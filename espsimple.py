"""ESP Simple Devices"""

from typing import Any
from datetime import date, datetime
from decimal import Decimal

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import EntityPlatform
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.entity import DeviceInfo
from .persistent_storage import ESPSimpleStorage


class ESPSimpleDeviceRegistry:
    """ESPSimpleDeviceHandler"""

    device_list: list = list()

    @staticmethod
    def add_device(device: Any) -> None:
        """Adds devices"""
        ESPSimpleDeviceRegistry.device_list.append(device)

    @staticmethod
    def get_device(id_str: str) -> Any:
        """Gets devices"""
        for d in ESPSimpleDeviceRegistry.device_list:
            if d.device_id == id_str:
                return d

    @staticmethod
    def remove_device(id_str: str) -> None:
        """Removes devices"""
        for d in ESPSimpleDeviceRegistry.device_list:
            if d.unique_id == id_str:
                ESPSimpleDeviceRegistry.device_list.remove(d)


class ESPSimpleDevice:
    def __init__(
        self,
        device_id: str,
        friendly_name: str,
        model: str,
        sw_version: str,
        entity_platform: EntityPlatform,
    ) -> None:
        self.device_id: str = device_id
        self.friendly_name: str = friendly_name
        self.model: str = model
        self.sw_version: str = sw_version
        self.entity_platform: EntityPlatform = entity_platform
        self.sensors: list = list()

    def get_sensor(self, id: str) -> Any:
        """Gets sensor by id of this device"""
        for s in self.sensors:
            if s.unique_id == id:
                return s

    def add_sensor(self, sensor: Any, add_entity: bool = True) -> None:
        """Adds discovered sensor to device"""
        self.sensors.append(sensor)
        if add_entity:
            self.entity_platform.add_entities([sensor])


class ESPSimpleSensorInfo:
    def __init__(
        self,
        name: str,
        unique_id: str,
        device: ESPSimpleDevice,
        unit_of_measurement: str,
        device_class: SensorDeviceClass,
        state_class: SensorStateClass,
    ) -> None:
        self.name: str = name
        self.unique_id: str = unique_id
        self.device: ESPSimpleDevice = device
        self.unit_of_measurement: str = unit_of_measurement
        self.device_class: SensorDeviceClass = device_class
        self.state_class: SensorStateClass = state_class


class ESPSimpleSensor(SensorEntity):
    """Representation of a Sensor."""

    def __init__(self, hass: HomeAssistant, info: ESPSimpleSensorInfo) -> None:
        self.hass: HomeAssistant = hass
        self.info: ESPSimpleSensorInfo = info
        self.state_value: str = ""

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        try:
            return float(self.state_value)
        except ValueError:
            return self.state_value

    @property
    def state_class(self) -> SensorStateClass | str | None:
        try:
            return SensorStateClass(self.info.state_class)
        except:
            return None

    @property
    def device_class(self) -> SensorDeviceClass | None:
        try:
            return SensorDeviceClass(self.info.device_class)
        except:
            return None

    @property
    def native_unit_of_measurement(self) -> str | None:
        return self.info.unit_of_measurement.strip()

    @property
    def unique_id(self) -> str | None:
        return self.info.device.device_id + "_" + self.info.unique_id

    @property
    def name(self) -> str | None:
        return self.info.name

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                ("espsimple", self.info.device.device_id)
            },
            name=self.info.device.friendly_name,
            manufacturer="ESP Simple Devices",
            model=self.info.device.model,
            sw_version=self.info.device.sw_version,
            via_device=("espsimple", self.info.device.device_id),
        )

    def set_state(self, state, set_state: bool = True):
        if set_state:
            state_attrs = self.hass.states.get(self.entity_id).attributes
            self.hass.states.set(
                self.entity_id,
                state,
                attributes=state_attrs,
            )
        self.state_value = state
