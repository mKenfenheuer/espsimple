import socket
import threading
from homeassistant.core import logging
from homeassistant.core import HomeAssistant
from .sensor import DEVICE_LIST


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
        logging.info(f"Connected by {addr}")
        while True:
            data = client.recv(6)

            if not data:
                break
            client.sendall(data)

    def server_thread(self) -> None:
        """Server Thread for accepting devices"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            while True:
                conn, addr = s.accept()
                client_thread = threading.Thread(
                    target=self.client_thread, args=(conn, addr)
                )

    def start(self) -> None:
        """Start the server"""
        logging.info("Socket server started")
        self.server_thread_obj = threading.Thread(target=self.server_thread)
