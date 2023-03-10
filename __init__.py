"""The ESP Simple Devices integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from .socket_server import ESPSimpleSocketServer
from homeassistant.components import zeroconf
from zeroconf.asyncio import AsyncServiceInfo
from homeassistant.core import logging
from homeassistant.components.network import async_get_enabled_source_ips
from .espsimple import *

import socket

from .const import DOMAIN

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [Platform.SENSOR]

__SOCKET_SERVER__: ESPSimpleSocketServer | None = None


async def register_service(hass: HomeAssistant):
    aiozc = await zeroconf.async_get_async_instance(hass)
    ip_list = await async_get_enabled_source_ips(hass)

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
        await register_service(hass)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        device = ESPSimpleDeviceRegistry.get_device(entry.data["device_id"])
        ESPSimpleDeviceRegistry.remove_device(entry.data["device_id"])
        device.remove_all_sensors()

    ESPSimpleStorage.set_devices(ESPSimpleDeviceRegistry.device_list)

    return unload_ok
