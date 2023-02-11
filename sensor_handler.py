from typing import Any
from homeassistant.core import logging


class ESPSimpleSensorHandler:
    """ESPSimpleSensorHandler"""

    device_list: list = list()

    @staticmethod
    def add_device(device) -> None:
        """Adds devices"""
        ESPSimpleSensorHandler.device_list.append(device)

    @staticmethod
    def get_device(id_str: str) -> Any:
        """Gets devices"""
        for d in ESPSimpleSensorHandler.device_list:
            if d.unique_id == id_str:
                return d
