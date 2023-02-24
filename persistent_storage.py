"""ESP Simple Devices persistent storage"""
import json
import os
from typing import Any


class ESPSimpleStorage:
    """ESPSimpleStorage"""

    config_file: str = "/config/.storage/espsimple.json"

    @staticmethod
    def init_storage(directory: str) -> None:
        """Initializes storage"""
        ESPSimpleStorage.config_file = directory + "/.storage/espsimple.json"
        if not os.path.isfile(ESPSimpleStorage.config_file):
            try:
                with open(
                    ESPSimpleStorage.config_file, mode="w+", encoding="utf-8"
                ) as f:
                    f.write("{}")
                    f.flush()
                    f.close()
            except OSError:
                return None

    @staticmethod
    def wipe_storage() -> None:
        """Wipes storage"""
        try:
            with open(ESPSimpleStorage.config_file, mode="w+", encoding="utf-8") as f:
                f.write("{}")
                f.flush()
                f.close()
        except OSError:
            return None

    @staticmethod
    def get_devices() -> Any:
        """Gets devices from storage"""
        if not os.path.isfile(ESPSimpleStorage.config_file):
            return None
        try:
            with open(ESPSimpleStorage.config_file, mode="r", encoding="utf-8") as f:
                storage_json = json.load(f)
                return storage_json["devices"]
        except OSError:
            return None
        except json.decoder.JSONDecodeError:
            ESPSimpleStorage.wipe_storage()
            return None

    @staticmethod
    def set_devices(devices) -> Any:
        """Sets devices to storage"""
        if not os.path.isfile(ESPSimpleStorage.config_file):
            return None
        try:
            with open(ESPSimpleStorage.config_file, mode="r", encoding="utf-8") as f:
                storage_json = json.load(f)
        except OSError:
            return None
        except json.decoder.JSONDecodeError:
            ESPSimpleStorage.wipe_storage()
            storage_json = json.loads("{}")
            return None

        device_list = list()
        for device in devices:
            sensor_list = list()
            for sensor in device.sensors:
                sensor_list.append(
                    {
                        "name": sensor.info.name,
                        "unique_id": sensor.info.unique_id,
                        "unit_of_measurement": sensor.info.unit_of_measurement,
                        "device_class": sensor.info.device_class,
                        "state_class": sensor.info.state_class,
                        "last_state": sensor.native_value,
                    }
                )
            device_list.append(
                {
                    "device_id": device.device_id,
                    "friendly_name": device.friendly_name,
                    "model": device.model,
                    "sw_version": device.sw_version,
                    "sensors": sensor_list,
                }
            )
        storage_json["devices"] = device_list

        try:
            with open(ESPSimpleStorage.config_file, mode="w+", encoding="utf-8") as f:
                json.dump(storage_json, f)
                f.flush()
                f.close()
        except OSError:
            return None

    @staticmethod
    def get_device(device_id) -> Any:
        """Get device info from storage"""
        if not os.path.isfile(ESPSimpleStorage.config_file):
            return None
        try:
            with open(ESPSimpleStorage.config_file, mode="r", encoding="utf-8") as f:
                storage_json = json.load(f)
        except OSError:
            return None
        except json.decoder.JSONDecodeError:
            ESPSimpleStorage.wipe_storage()
            storage_json = json.loads("{}")
            return None

        devices = storage_json["devices"]

        for d in devices:
            if d["device_id"] == device_id:
                return d
