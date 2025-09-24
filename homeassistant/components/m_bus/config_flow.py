"""Config flow for the M-Bus integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from propcache.api import cached_property
import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    SubentryFlowResult,
)
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.selector import selector

from .const import (
    CONF_MBUS_SERIAL_PROTOCOL,
    DOMAIN,
    MBUS_DEFAULT_SOCKET_PORT,
    MBUS_KEY_IDENTIFICATION,
    MBUS_KEY_MANUFACTURER,
    MBUS_KEY_MEDIUM,
    MBUS_KEY_VERSION,
    MBUS_MEDIUM_TYPES,
    MBUS_SERIAL_PROTOCOL_SOCKET,
)
from .coordinator import MBusCoordinator

_LOGGER = logging.getLogger(__name__)


class MBusMasterConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for M-Bus."""

    VERSION = 1

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of the integration."""
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            # Check for duplicate entries using unique data pattern
            # (automatically ignores current entry when in reconfigure context)
            self._async_abort_entries_match(
                {
                    CONF_HOST: user_input[CONF_HOST],
                    CONF_PORT: user_input[CONF_PORT],
                }
            )

            # Only test connection if host or port actually changed
            connection_changed = (
                user_input[CONF_HOST] != entry.data[CONF_HOST] or
                user_input[CONF_PORT] != entry.data[CONF_PORT]
            )

            if connection_changed:
                # Perform validation (connection test required)
                try:
                    await self._async_validate_input(user_input)
                except CannotConnect:
                    errors["base"] = "cannot_connect"
                except Exception:
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"

            # If no errors (either no change or successful validation)
            if not errors:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PORT: user_input[CONF_PORT],
                    },
                )

        return self.async_show_form(
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(
                    {
                        vol.Required(CONF_HOST): str,
                        vol.Required(CONF_PORT): cv.port,
                    }
                ),
                user_input
                if user_input is not None
                else {
                    CONF_HOST: entry.data[CONF_HOST],
                    CONF_PORT: entry.data[CONF_PORT],
                },
            ),
            errors=errors,
            description_placeholders={"name": entry.title},
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Check for duplicate entries using unique data pattern
            self._async_abort_entries_match(
                {
                    CONF_MBUS_SERIAL_PROTOCOL: MBUS_SERIAL_PROTOCOL_SOCKET,
                    CONF_HOST: user_input[CONF_HOST],
                    CONF_PORT: user_input[CONF_PORT],
                }
            )

            # Perform validation (connection test required)
            try:
                await self._async_validate_input(user_input)
                return self.async_create_entry(
                    title=f"{MBUS_SERIAL_PROTOCOL_SOCKET}://{user_input[CONF_HOST]}:{user_input[CONF_PORT]}",
                    data={
                        CONF_MBUS_SERIAL_PROTOCOL: MBUS_SERIAL_PROTOCOL_SOCKET,
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PORT: user_input[CONF_PORT],
                    },
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(
                    {
                        vol.Required(CONF_HOST): str,
                        vol.Required(
                            CONF_PORT, default=MBUS_DEFAULT_SOCKET_PORT
                        ): cv.port,
                    }
                ),
                user_input,
            ),
            errors=errors,
        )

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        """Return subentries supported by this integration."""
        return {"meter": MBusMeterSubentryFlowHandler}

    @staticmethod
    def _test_serial_connection_sync(protocol: str, host: str, port: int) -> None:
        """Test serial connection (static, runs in executor)."""
        # Use coordinator's static method to create serial
        serial = MBusCoordinator.create_serial_instance(protocol, host, port)

        try:
            serial.open()  # Test actual connection
        finally:
            if serial.is_open:
                serial.close()

    async def _async_validate_input(self, data: dict[str, Any]) -> None:
        """Validate the user input allows us to connect."""

        # Test if we can open serial connection
        try:
            # Pass connection data to executor - do ALL serial work there
            await self.hass.async_add_executor_job(
                self._test_serial_connection_sync,
                MBUS_SERIAL_PROTOCOL_SOCKET,
                data[CONF_HOST],
                data[CONF_PORT],
            )
        except Exception as err:
            raise CannotConnect from err


class MBusMeterSubentryFlowHandler(ConfigSubentryFlow):
    """Handle meter subentry flow for M-Bus."""

    _progress_task: asyncio.Task | None = None

    _target_address: int | None = None

    @cached_property
    def _coordinator(self) -> MBusCoordinator:
        """Get the coordinator from the config entry."""
        return self._get_entry().runtime_data

    @cached_property
    def _found_meters(self) -> dict[int, dict[str, Any] | None]:
        """Get discovered meters from the coordinator."""
        return self._coordinator.found_meters

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Initial step where user chooses to add meter based on address, select meter from list or search for meters."""

        return self.async_show_menu(
            step_id="user",
            menu_options=["address", "select", "search"],
        )

    async def async_step_address(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Add a M-Bus meter by specifying its address."""

        if self._progress_task is not None:
            # We have an ongoing manual add task

            if not self._progress_task.done():
                # Task is still running, show progress again
                return self.async_show_progress(
                    step_id="address",
                    progress_action="querying_address",
                    progress_task=self._progress_task,
                )

            # Task is done, clear the task
            self._progress_task = None

            # Go to add meter step. Validation of meter, if any was found, will be done there.
            return self.async_show_progress_done(next_step_id="add_meter")

        if user_input is not None:
            # User submitted the form. Query the specified address.

            self._target_address = user_input["bus_address"]

            # Create the query task
            self._progress_task = self.hass.async_create_task(
                self._coordinator.async_scan_bus_address_range(
                    start_address=self._target_address,
                    end_address=self._target_address,
                    callback=None,
                ),
                eager_start=False,
            )

            # Show progress
            return self.async_show_progress(
                step_id="address",
                progress_action="querying_address",
                progress_task=self._progress_task,
            )

        return self.async_show_form(
            step_id="address",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(
                    {
                        vol.Required("bus_address", default=1): vol.All(
                            selector(
                                {
                                    "number": {
                                        "min": 1,
                                        "max": 250,
                                        "step": 1,
                                        "mode": "box",
                                    }
                                }
                            ),
                            vol.Coerce(int),
                        ),
                    }
                ),
                user_input,
            ),
            last_step=False,
        )

    async def async_step_select(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Show search results and allow meter selection."""

        if len(self._found_meters) == 0:
            # No addresses have been searched yet. Suggest doing a search first.
            return await self.async_step_no_search_yet()

        errors = {}

        if user_input is not None:
            # User submitted the form
            if user_input["target_address"] is None:
                # No meter selected
                errors["target_address"] = "no_meter_selected"

            self._target_address = user_input["target_address"]

            return await self.async_step_add_meter()

        # Create selection schema for discovered meters
        addable_meter_options = []

        bus_searched_count = 0
        total_meter_count = 0
        addable_meter_count = 0

        # Get existing subentries to check for duplicates
        existing_unique_ids = {
            subentry.unique_id for subentry in self._get_entry().subentries.values()
        }

        for meter_address, meter_data in self._found_meters.items():
            bus_searched_count += 1
            if meter_data is not None:
                total_meter_count += 1
                # Check if meter is already configured as subentry
                if str(meter_address) not in existing_unique_ids:
                    addable_meter_count += 1
                    # TODO Improve label and make translatable
                    addable_meter_options.append(
                        {
                            "label": f"{meter_address}: {MBUS_MEDIUM_TYPES.get(meter_data[MBUS_KEY_MEDIUM], f'Unknown ({meter_data[MBUS_KEY_MEDIUM]})')} [manufacturer: {meter_data[MBUS_KEY_MANUFACTURER]}, identification: {meter_data[MBUS_KEY_IDENTIFICATION]}, version: {meter_data[MBUS_KEY_VERSION]}]",
                            "value": str(meter_address),
                        }
                    )

        if total_meter_count == 0:
            # No meters found at all. Suggest doing a search again.
            return await self.async_step_nothing_found()

        if addable_meter_count == 0:
            # All found meters are already configured as subentries. Suggest doing a search again.
            return await self.async_step_nothing_available()

        return self.async_show_form(
            step_id="select",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "target_address", addable_meter_options[0]["value"]
                    ): vol.All(
                        selector(
                            {
                                "select": {
                                    "options": addable_meter_options,
                                    "mode": "dropdown",
                                }
                            }
                        ),
                        vol.Coerce(int),
                    ),
                }
            ),
            description_placeholders={
                "master_name": self._get_entry().title,
                "total_meter_count": str(total_meter_count),
                "addable_meter_count": str(addable_meter_count),
                "bus_searched_count": str(bus_searched_count),
                "total_bus_addresses": "250",  # TODO Save as constant
            },
            last_step=False,
            errors=errors,
        )

    async def async_step_search(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Search for M-Bus meters on the bus."""

        if self._progress_task is not None:
            # We have an ongoing search task

            if not self._progress_task.done():
                # Task is still running, show progress again
                return self.async_show_progress(
                    step_id="search",
                    progress_action="searching_meters",
                    progress_task=self._progress_task,
                )

            # Task is done, clear the task
            self._progress_task = None

            # Go to select meter step
            return self.async_show_progress_done(next_step_id="select")

        errors = {}

        if user_input is not None:
            # User submitted the form, validate and start search if no errors
            if user_input["start_address"] > user_input["end_address"]:
                errors["start_address"] = "start_before_end"
                errors["end_address"] = "end_before_start"

            if not errors:
                # Create the search task
                self._progress_task = self.hass.async_create_task(
                    self._coordinator.async_scan_bus_address_range(
                        start_address=user_input["start_address"],
                        end_address=user_input["end_address"],
                        callback=self.async_update_progress
                        if user_input["start_address"] != user_input["end_address"]
                        else None,
                    ),
                    eager_start=False,
                )

                # Show progress
                return self.async_show_progress(
                    step_id="search",
                    progress_action="searching_meters",
                    progress_task=self._progress_task,
                )

        # Show the form (first time or if there were errors)
        return self.async_show_form(
            step_id="search",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(
                    {
                        vol.Required("start_address", default=1): vol.All(
                            selector(
                                {
                                    "number": {
                                        "min": 1,
                                        "max": 250,
                                        "step": 1,
                                        "mode": "box",
                                    }
                                }
                            ),
                            vol.Coerce(int),
                        ),
                        vol.Required("end_address", default=250): vol.All(
                            selector(
                                {
                                    "number": {
                                        "min": 1,
                                        "max": 250,
                                        "step": 1,
                                        "mode": "box",
                                    }
                                }
                            ),
                            vol.Coerce(int),
                        ),
                    }
                ),
                user_input,
            ),
            last_step=False,
            errors=errors,
        )

    async def async_step_no_search_yet(self) -> SubentryFlowResult:
        """Inform user that no search for meters has been done yet and suggest to do a search."""

        return self.async_show_menu(
            step_id="no_search_yet",
            menu_options=["search"],
        )

    async def async_step_nothing_found(self) -> SubentryFlowResult:
        """Inform user that no meters were found and suggest to do a search."""

        return self.async_show_menu(
            step_id="nothing_found",
            menu_options=["search"],
        )

    async def async_step_nothing_available(self) -> SubentryFlowResult:
        """Inform user that no meters are available for addition and suggest to do a search."""

        return self.async_show_menu(
            step_id="nothing_available",
            menu_options=["search"],
        )

    async def async_step_add_meter(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Add a M-Bus meter."""
        if self._target_address is None:
            # This should not happen, but just in case
            return self.async_abort(reason="unknown")

        if self._found_meters.get(self._target_address) is None:
            # No meter found at the specified address. This should only happen if user manually
            # entered an address but no meter was found at that address.
            return self.async_abort(
                reason="nothing_to_add",
            )

        # Check if this bus address is already configured as a subentry
        for existing_subentry in self._get_entry().subentries.values():
            if existing_subentry.unique_id == str(self._target_address):
                return self.async_abort(
                    reason="already_configured",
                )

        if user_input is not None:
            # Create a device config entry
            return self.async_create_entry(
                title=f"M-Bus Device (Address {self._target_address})",
                data={
                    "bus_address": self._target_address,
                    "name": user_input.get(
                        "name", f"M-Bus Device {self._target_address}"
                    ),
                },
                unique_id=str(self._target_address),  # Unique per master entry
            )

        return self.async_show_form(
            step_id="add_meter",
            data_schema=vol.Schema(
                {
                    vol.Optional("name"): str,
                }
            ),
            description_placeholders={"master_name": self._get_entry().title},
            last_step=True,
            errors={},
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
