"""The ESP Simple Devices integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from .socket_server import ESPSimpleSocketServer
from homeassistant.components import zeroconf
from zeroconf.asyncio import AsyncServiceInfo
from homeassistant.core import logging

import socket

from .const import DOMAIN

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [Platform.SENSOR]

__SOCKET_SERVER__: ESPSimpleSocketServer | None = None


async def register_service(hass: HomeAssistant):
    aiozc = await zeroconf.async_get_async_instance(hass)
    ip_list = list()
    adapters = hass.data["network"].adapters
    for adapter in adapters:
        for ip in adapter["ipv4"]:
            if ip["address"] != "127.0.0.1":
                logging.info(
                    "Registering zeroconf service _espsmplsrvr for host "
                    + hass.data["core.uuid"]
                    + " on IP "
                    + ip["address"]
                )
                ip_list.append(socket.inet_aton(ip["address"]))
    info = AsyncServiceInfo(
        type_="_espsmplsrvr._tcp.local.",
        name=hass.data["core.uuid"] + "._espsmplsrvr._tcp.local.",
        addresses=ip_list,
        port=8901,
        properties={},
    )
    await aiozc.async_register_service(info)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ESP Simple Devices from a config entry."""
    global __SOCKET_SERVER__

    if __SOCKET_SERVER__ is None:
        __SOCKET_SERVER__ = ESPSimpleSocketServer(hass)
        __SOCKET_SERVER__.start()

    hass.data.setdefault(DOMAIN, {})
    # TODO 1. Create API instance
    # TODO 2. Validate the API connection (and authentication)
    # TODO 3. Store an API object for your platforms to access
    # hass.data[DOMAIN][entry.entry_id] = MyApi(...)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await register_service(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
