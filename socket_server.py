import socket
import threading
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import logging
from homeassistant.core import HomeAssistant
from .espsimple import (
    ESPSimpleSensor,
    ESPSimpleSensorInfo,
    ESPSimpleDevice,
    ESPSimpleDeviceRegistry,
)
from .persistent_storage import ESPSimpleStorage

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)


class ESPSimpleSocketServer:
    """TCP Socket Server for ESPSimpleDevices"""

    def __init__(
        self, hass: HomeAssistant, host: str = "0.0.0.0", port: int = 8901
    ) -> None:
        self.host: str = host
        self.port: int = port
        self.hass: HomeAssistant = hass
        ESPSimpleStorage.init_storage(hass.config.config_dir)

    def create_and_add_sensor(
        self,
        device: ESPSimpleDevice,
        display_name: str,
        unique_id: str,
        unit_of_measurement: str,
        device_class: SensorDeviceClass,
        state_class: SensorStateClass,
    ) -> ESPSimpleSensor:
        """Creates and adds sensors"""
        sensor: ESPSimpleSensor = ESPSimpleSensor(
            self.hass,
            ESPSimpleSensorInfo(
                device.friendly_name + " " + display_name,
                unique_id,
                device,
                unit_of_measurement,
                device_class,
                state_class,
            ),
        )

        device.add_sensor(sensor)
        ESPSimpleStorage.set_devices(ESPSimpleDeviceRegistry.device_list)

        return sensor

    def read_string(self, client) -> str:
        length_data = client.recv(4)
        if not length_data:
            return None

        length = int.from_bytes(length_data, "little")

        string_data = client.recv(length)
        if not length_data:
            return None

        string = string_data.decode("utf-8")

        return string

    def handle_registration(self, client, addr) -> None:
        """Handles sensor registration messages"""
        device_id = self.read_string(client)
        if not id:
            return

        sensor_id = self.read_string(client)
        if not sensor_id:
            return

        display_name = self.read_string(client)
        if not display_name:
            return

        unit = self.read_string(client)
        if not unit:
            return

        state_class = self.read_string(client)
        if not state_class:
            return

        device_class = self.read_string(client)
        if not device_class:
            return

        device = ESPSimpleDeviceRegistry.get_device(device_id)
        if not device:
            return

        sensor: ESPSimpleSensor = device.get_sensor(device_id + "_" + sensor_id)
        if not sensor:
            sensor = self.create_and_add_sensor(
                device, display_name, sensor_id, unit, device_class, state_class
            )
        else:
            sensor.info.device_class = device_class
            sensor.info.name = display_name
            sensor.info.state_class = state_class
            sensor.info.unit_of_measurement = unit

        client.sendall(bytes([1]))

    def handle_update(self, client, addr) -> None:
        """Handles state updates"""

        device_id = self.read_string(client)
        if not device_id:
            return

        sensor_id = self.read_string(client)
        if not sensor_id:
            return

        state = self.read_string(client)
        if not state:
            return

        logging.info(
            "Device " + device_id + " reported state " + state + " for uid " + sensor_id
        )

        client.sendall(bytes([1]))

        device = ESPSimpleDeviceRegistry.get_device(device_id)
        if not device:
            return

        sensor = device.get_sensor(device_id + "_" + sensor_id)
        if not sensor:
            return

        sensor.set_state(state)
        ESPSimpleStorage.set_devices(ESPSimpleDeviceRegistry.device_list)

    def client_thread(self, client, addr) -> None:
        """Client thread method"""
        type = client.recv(1)
        if not type:
            return

        if type[0] is 0:
            self.handle_registration(client, addr)

        if type[0] is 1:
            self.handle_update(client, addr)

    def server_thread(self) -> None:
        """Server Thread for accepting devices"""
        logging.info("Socket server started")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            while True:
                conn, addr = s.accept()
                client_thread = threading.Thread(
                    target=self.client_thread, args=(conn, addr)
                )
                client_thread.start()

    def start(self) -> None:
        """Start the server"""
        self.server_thread_obj = threading.Thread(target=self.server_thread)
        self.server_thread_obj.start()
