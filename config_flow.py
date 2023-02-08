"""Config flow for ESP Simple Devices integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

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
        # The device name as per its config
        self.device_name: str | None = None

    async def async_step_encryption_key(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        self.encryption_key = user_input["encryption_key"]
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
            config = {
                "host": self.host,
                "port": self.port,
                "name": self.name,
                "encryption_key": self.encryption_key,
                "encrypted": self.encrypted,
            }
            return self.async_create_entry(title=self.name, data=config)

        return self.async_show_form(
            step_id="encryption_key",
            errors=errors,
        )

    async def async_step_discovery_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle user-confirmation of discovered node."""

        if self.encrypted is True:
            return self.async_show_form(
                step_id="encryption_key",
                data_schema=vol.Schema({vol.Required("encryption_key"): str}),
            )

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
            config = {
                "host": self.host,
                "port": self.port,
                "name": self.name,
                "encryption_key": self.encryption_key,
                "encrypted": self.encrypted,
            }
            return self.async_create_entry(title=self.name, data=config)

        return self.async_show_form(
            step_id="discovery_confirm",
            description_placeholders={"name": self.name},
            errors=errors,
        )

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
        self.encrypted = True

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
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        # Hostname is format: livingroom.local.
        device_name = user_input["host"]

        self.name = device_name
        self.device_name = device_name
        self.host = device_name
        self.port = 80
        self.encrypted = False

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
            config = {
                "host": self.host,
                "port": self.port,
                "name": self.name,
                "encryption_key": self.encryption_key,
                "encrypted": self.encrypted,
            }
            return self.async_create_entry(title=self.name, data=config)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
