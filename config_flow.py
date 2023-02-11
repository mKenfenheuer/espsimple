"""Config flow for ESP Simple Devices integration."""
from __future__ import annotations

import logging
import json
import random
import string
from typing import Any

import voluptuous as vol
import requests

from homeassistant.components import zeroconf
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# TODO adjust the data schema to the data that you need
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("host"): str,
    }
)


class PlaceholderHub:
    """Placeholder class to make tests pass.

    TODO Remove this placeholder class and replace with things from your PyPI package.
    """

    def __init__(self, host: str) -> None:
        """Initialize."""
        self.host = host

    async def authenticate(self, encryption_key: str) -> bool:
        """Test if we can authenticate with the host."""
        return True


async def validate_input(hass: HomeAssistant, flow: ConfigFlow):
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # TODO validate the data can be used to set up a connection.

    # If your PyPI package is not built with async, pass your methods
    # to the executor:
    # await hass.async_add_executor_job(
    #     your_validate_func, data["username"], data["password"]
    # )

    hub = PlaceholderHub(flow.host)

    if flow.encrypted is True:
        if not await hub.authenticate(flow.encryption_key):
            raise InvalidAuth

    # If you cannot connect:
    # throw CannotConnect
    # If the authentication is wrong:
    # InvalidAuth


def get_device_info(flow: ConfigFlow):
    url = "http://" + flow.host + ":" + str(flow.port) + "/info"
    info = requests.get(url)

    if info.status_code != 200:
        return None

    infojson = info.json()

    if "friendly_name" in infojson:
        flow.name = infojson["friendly_name"]
    if "device_id" not in infojson:
        raise Exception("No device_id specified.")
    if "sensors" not in infojson:
        raise Exception("No sensors defined.")

    flow.info = infojson


def get_random_string(length) -> str:
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = "".join(random.choice(letters) for i in range(length))
    return result_str


def adopt_device(flow: ConfigFlow):
    flow.info = flow.info
    flow.config = {
        "encryption_key": get_random_string(16),
        "host": flow.host,
        "port": flow.port,
        "device_name": flow.device_name,
        "device_id": flow.info["device_id"],
        "friendly_name": flow.name,
        "sensors": flow.info["sensors"],
    }
    url = "http://" + flow.host + ":" + str(flow.port) + "/adopt"
    response = requests.post(
        url, data={"ha_instance": "hello", "key": flow.config["encryption_key"]}
    )
    if response.status_code != 200:
        flow.errors["base"] = "Could not adopt device. Code: " + str(
            response.status_code
        )


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ESP Simple Devices."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow."""
        self.host: str | None = None
        self.port: int | None = None
        self.encryption_key: str | None = None
        self.encrypted: bool | None = None
        self.name: str | None = None
        self.info: Any = None
        self.config: Any = None
        # The device name as per its config
        self.device_name: str | None = None

    async def async_step_device_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is None:
            return self.async_show_form(
                step_id="device_settings",
                data_schema=vol.Schema(
                    {vol.Required("friendly_name", default=self.name): str}
                ),
                description_placeholders={"name": self.name},
            )

        if "friendly_name" in user_input:
            self.name = user_input["friendly_name"]

        errors = {}

        try:
            await validate_input(self.hass, self)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            await self.hass.async_add_executor_job(adopt_device, self)
            return self.async_create_entry(title=self.name, data=self.config)

        return self.async_show_form(
            step_id="device_settings",
            data_schema=vol.Schema(
                {vol.Required("friendly_name", default=self.name): str}
            ),
            errors=errors,
        )

    async def async_step_discovery_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle user-confirmation of discovered node."""

        if user_input is None:
            return self.async_show_form(
                step_id="discovery_confirm",
                description_placeholders={"name": self.name},
            )

        await self.hass.async_add_executor_job(get_device_info, self)

        return await self.async_step_device_settings()

    async def async_step_zeroconf(
        self, discovery_info: zeroconf.ZeroconfServiceInfo
    ) -> FlowResult:
        """Handle zeroconf discovery."""

        # Hostname is format: livingroom.local.
        device_name = discovery_info.hostname.removesuffix(".local.")

        self.name = discovery_info.properties.get("friendly_name", device_name)
        self.device_name = device_name
        self.host = discovery_info.host
        self.port = discovery_info.port

        # Check if already configured
        await self.async_set_unique_id(device_name)
        self._abort_if_unique_id_configured(
            updates={CONF_HOST: self.host, CONF_PORT: self.port}
        )

        return await self.async_step_discovery_confirm()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=vol.Schema({vol.Required("host"): str})
            )

        # Hostname is format: livingroom.local.
        device_name = user_input["host"]

        self.name = device_name
        self.device_name = device_name
        self.host = device_name
        self.port = 8901

        await self.hass.async_add_executor_job(get_device_info, self)

        errors = {}

        try:
            await validate_input(self.hass, self)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return await self.async_step_device_settings()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
