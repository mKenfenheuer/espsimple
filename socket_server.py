import socket
import threading
from homeassistant.core import logging
from homeassistant.core import HomeAssistant
from .sensor_handler import ESPSimpleSensorHandler


class ESPSimpleSocketServer:
    """TCP Socket Server for ESPSimpleDevices"""

    def __init__(
        self, hass: HomeAssistant, host: str = "0.0.0.0", port: int = 8901
    ) -> None:
        self.host: str = host
        self.port: int = port
        self.hass: HomeAssistant = hass

    def client_thread(self, client, addr) -> None:
        """Client thread method"""
        id = client.recv(12)
        if not id:
            return
        id_str = id.decode("utf-8")

        len1 = client.recv(4)
        if not len1:
            return
        length1 = int.from_bytes(len1, "little")

        uid = client.recv(length1)
        uid_str = uid.decode("utf-8")

        len2 = client.recv(4)
        if not len2:
            return
        length2 = int.from_bytes(len2, "little")

        state = client.recv(length2)
        state_str = state.decode("utf-8")

        logging.info(
            "Device " + id_str + " reported state " + state_str + " for uid " + uid_str
        )

        client.sendall(bytes([1]))

        device = ESPSimpleSensorHandler.get_device(id_str + "_" + uid_str)
        if not device:
            return
        device.set_state(state_str)

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
