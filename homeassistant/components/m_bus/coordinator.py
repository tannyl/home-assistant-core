"""M-Bus data coordinator."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import timedelta
import logging
import re
from typing import Any

import meterbus
from propcache.api import cached_property
import serial
from serial import EIGHTBITS, PARITY_EVEN, STOPBITS_ONE

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_MBUS_SERIAL_PROTOCOL,
    DOMAIN,
    MBUS_KEY_IDENTIFICATION,
    MBUS_KEY_MANUFACTURER,
    MBUS_KEY_MEDIUM,
    MBUS_KEY_RECORDS,
    MBUS_KEY_VERSION,
)

_LOGGER = logging.getLogger(__name__)


type MBusConfigEntry = ConfigEntry[MBusCoordinator]


class MBusCoordinator(DataUpdateCoordinator[dict[int, Any]]):
    """M-Bus data coordinator."""

    config_entry: ConfigEntry
    found_meters: dict[int, dict[str, Any] | None]
    _bus_lock: asyncio.Lock

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize M-Bus coordinator."""
        _LOGGER.debug("__init__: hass=%s, config_entry=%s", hass, config_entry.entry_id)
        self.config_entry = config_entry
        self.found_meters = {}
        self._bus_lock = asyncio.Lock()

        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN}_{config_entry.entry_id}",
            update_interval=timedelta(minutes=5),
            config_entry=config_entry,
        )

    @cached_property
    def _serial(self) -> serial.Serial:
        """Get configured serial object (only call from executor methods)."""
        return self.create_serial_instance(
            self.config_entry.data[CONF_MBUS_SERIAL_PROTOCOL],
            self.config_entry.data[CONF_HOST],
            self.config_entry.data[CONF_PORT],
        )

    @staticmethod
    def create_serial_instance(protocol: str, host: str, port: int) -> serial.Serial:
        """Create and return a serial.Serial instance (only call from executor methods)."""
        return serial.serial_for_url(
            f"{protocol}://{host}:{port}",
            bytesize=EIGHTBITS,
            parity=PARITY_EVEN,
            stopbits=STOPBITS_ONE,
            baudrate=2400,  # M-Bus standard
            timeout=1.0,
            do_not_open=True,
        )

    async def _async_update_data(self) -> dict[int, Any]:
        """Fetch data from M-Bus gateway."""
        _LOGGER.debug("_async_update_data")
        # Mock data for sensor development and testing
        return self._get_mock_meter_data()

    def _get_mock_meter_data(self) -> dict[int, Any]:
        """Return mock meter data for sensor development."""
        return {
            # Water meter at address 1
            1: {
                MBUS_KEY_MANUFACTURER: "ABC",
                MBUS_KEY_IDENTIFICATION: "12345678",
                MBUS_KEY_VERSION: 1,
                MBUS_KEY_MEDIUM: 0x07,  # Water
                MBUS_KEY_RECORDS: {
                    "0_Volume_m3_Instantaneous value": {
                        "value": 1234.567,
                        "unit": "MeasureUnit.M3",
                        "type": "Volume",
                        "storage_number": 0,
                        "function": "Instantaneous value",
                    },
                    "0_Volume flow_m3/h_Instantaneous value": {
                        "value": 2.5,
                        "unit": "MeasureUnit.M3_H",
                        "type": "Volume flow",
                        "storage_number": 0,
                        "function": "Instantaneous value",
                    },
                    "0_Flow temperature_°C_Instantaneous value": {
                        "value": 18.5,
                        "unit": "MeasureUnit.C",
                        "type": "Flow temperature",
                        "storage_number": 0,
                        "function": "Instantaneous value",
                    },
                },
            },
            # Heat meter at address 2
            2: {
                MBUS_KEY_MANUFACTURER: "DEF",
                MBUS_KEY_IDENTIFICATION: "87654321",
                MBUS_KEY_VERSION: 2,
                MBUS_KEY_MEDIUM: 0x04,  # Heat (Outgoing)
                MBUS_KEY_RECORDS: {
                    "0_Energy_Wh_Instantaneous value": {
                        "value": 15678.9,
                        "unit": "MeasureUnit.WH",
                        "type": "Energy Wh",
                        "storage_number": 0,
                        "function": "Instantaneous value",
                    },
                    "0_Energy_Wh_Maximum value": {
                        "value": 20000.0,
                        "unit": "MeasureUnit.WH",
                        "type": "Energy",
                        "storage_number": 0,
                        "function": "Maximum value",
                    },
                    "0_Power_W_Instantaneous value": {
                        "value": 3500.0,
                        "unit": "MeasureUnit.W",
                        "type": "Power W",
                        "storage_number": 0,
                        "function": "Instantaneous value",
                    },
                    "0_Flow temperature_°C_Instantaneous value": {
                        "value": 65.2,
                        "unit": "MeasureUnit.C",
                        "type": "Flow temperature",
                        "storage_number": 0,
                        "function": "Instantaneous value",
                    },
                    "0_Return temperature_°C_Instantaneous value": {
                        "value": 42.8,
                        "unit": "MeasureUnit.C",
                        "type": "Return temperature",
                        "storage_number": 0,
                        "function": "Instantaneous value",
                    },
                },
            },
            # Gas meter at address 3
            3: {
                MBUS_KEY_MANUFACTURER: "GHI",
                MBUS_KEY_IDENTIFICATION: "11223344",
                MBUS_KEY_VERSION: 1,
                MBUS_KEY_MEDIUM: 0x03,  # Gas
                MBUS_KEY_RECORDS: {
                    "0_Volume_m3_Instantaneous value": {
                        "value": 5678.123,
                        "unit": "MeasureUnit.M3",
                        "type": "Volume",
                        "storage_number": 0,
                        "function": "Instantaneous value",
                    },
                    "0_Volume flow_m3/h_Instantaneous value": {
                        "value": 1.8,
                        "unit": "MeasureUnit.M3_H",
                        "type": "Volume flow",
                        "storage_number": 0,
                        "function": "Instantaneous value",
                    },
                    "1_Volume_m3_Maximum value": {
                        "value": 6000.0,
                        "unit": "MeasureUnit.M3",
                        "type": "Volume",
                        "storage_number": 1,
                        "function": "Maximum value",
                    },
                },
            },
            # Electricity meter at address 4
            4: {
                MBUS_KEY_MANUFACTURER: "JKL",
                MBUS_KEY_IDENTIFICATION: "99887766",
                MBUS_KEY_VERSION: 3,
                MBUS_KEY_MEDIUM: 0x02,  # Electricity
                MBUS_KEY_RECORDS: {
                    "0_Energy_Wh_Instantaneous value": {
                        "value": 2345.6,
                        "unit": "MeasureUnit.KWH",
                        "type": "Energy Wh",
                        "storage_number": 0,
                        "function": "Instantaneous value",
                    },
                    "0_Power_W_Instantaneous value": {
                        "value": 1250.0,
                        "unit": "MeasureUnit.W",
                        "type": "Power W",
                        "storage_number": 0,
                        "function": "Instantaneous value",
                    },
                    "0_Volts_V_Instantaneous value": {
                        "value": 230.5,
                        "unit": "MeasureUnit.V",
                        "type": "Volts",
                        "storage_number": 0,
                        "function": "Instantaneous value",
                    },
                    "0_Ampere_A_Instantaneous value": {
                        "value": 5.43,
                        "unit": "MeasureUnit.A",
                        "type": "Ampere",
                        "storage_number": 0,
                        "function": "Instantaneous value",
                    },
                    "0_Energy_Wh_Maximum value": {
                        "value": 5000.0,
                        "unit": "MeasureUnit.KWH",
                        "type": "Energy Wh",
                        "storage_number": 0,
                        "function": "Maximum value",
                    },
                },
            },
        }

    async def async_query_bus_address_list(
        self, addresses: list[int]
    ) -> dict[int, Any] | None:
        """Query meter data for list of bus addresses."""
        async with self._bus_lock:
            return await self.hass.async_add_executor_job(
                self._query_bus_address_list_sync, addresses
            )

    def _query_bus_address_list_sync(self, addresses: list[int]) -> dict[int, Any]:
        """Query meter data for list of bus addresses (synchronous, runs in executor)."""
        results: dict[int, Any] = {}

        with self._serial as ser:
            for address in addresses:
                meter_data = self._query_bus_address_sync(ser, address)
                if meter_data is not None:
                    results[address] = meter_data

        return results

    async def async_scan_bus_address_range(
        self,
        start_address: int,
        end_address: int,
        callback: Callable[[float], None] | None,
    ) -> None:
        """Scan a range of bus addresses for connected meters and store results in found_meters. Calls the provided callback function after each address is scanned."""
        async with self._bus_lock:
            await self.hass.async_add_executor_job(
                self._scan_bus_address_range_sync, start_address, end_address, callback
            )

    def _scan_bus_address_range_sync(
        self,
        start_address: int,
        end_address: int,
        callback: Callable[[float], None] | None,
    ) -> None:
        """Scan a range of bus addresses (synchronous, runs in executor)."""
        with self._serial as ser:
            # Total addresses to scan
            total_addresses = end_address - start_address + 1

            if callback is not None:
                # First progress update - call safely from executor thread
                try:
                    self.hass.loop.call_soon_threadsafe(callback, 0.0)
                except Exception as err:  # noqa: BLE001
                    _LOGGER.warning("Error calling final progress callback: %s", err)

            for index, address in enumerate(range(start_address, end_address + 1), 1):
                # Set bus address to None initially
                self.found_meters[address] = None

                # Ping the address to see if a meter responds
                if self._ping_bus_address_sync(ser, address):
                    # If ping successful, query meter data
                    meter_data = self._query_bus_address_sync(ser, address)

                    if meter_data is not None:
                        # Store the found meter data in the coordinator's found_meters
                        self.found_meters[address] = {
                            MBUS_KEY_MANUFACTURER: meter_data[MBUS_KEY_MANUFACTURER],
                            MBUS_KEY_IDENTIFICATION: meter_data[
                                MBUS_KEY_IDENTIFICATION
                            ],
                            MBUS_KEY_VERSION: meter_data[MBUS_KEY_VERSION],
                            MBUS_KEY_MEDIUM: meter_data[MBUS_KEY_MEDIUM],
                        }

                if callback is not None:
                    # Update progress - call safely from executor thread
                    try:
                        self.hass.loop.call_soon_threadsafe(
                            callback, float(index / total_addresses)
                        )
                    except Exception as err:  # noqa: BLE001
                        _LOGGER.warning("Error calling progress callback: %s", err)

    @staticmethod
    def _ping_bus_address_sync(ser: serial.Serial, address: int) -> bool:
        """Send ping frame to address (synchronous, runs in executor)."""
        _LOGGER.debug("Pinging address: %d", address)
        assert ser.is_open

        # Clear serial input buffer
        ser.reset_input_buffer()

        # Retry ping up to 3 times
        for _ in range(3):
            try:
                # Send ping frame to address and receive response
                meterbus.send_ping_frame(ser, address)

                # Receive and load response frame
                frame = meterbus.load(meterbus.recv_frame(ser, 1))

                # Check if response is an ACK telegram
                if isinstance(frame, meterbus.TelegramACK):
                    return True
            except meterbus.MBusFrameDecodeError:
                # Silent retry on frame decode errors
                pass

        # All retries failed
        return False

    @staticmethod
    def _query_bus_address_sync(
        ser: serial.Serial, address: int, multi: bool = False, records: bool = False
    ) -> dict[str, Any] | None:
        """Query meter data (synchronous, runs in executor)."""
        _LOGGER.debug("Querying address: %d, multi: %s", address, multi)
        # Ensure connection is open
        assert ser.is_open

        # Clear serial input buffer
        ser.reset_input_buffer()

        # Maximum frames to prevent infinite loops from buggy meters
        MAX_FRAMES = 10

        try:
            # Send request based on multi-frame mode
            if multi:
                # Use multi-frame request with FCV and FCB set
                req = meterbus.send_request_frame_multi(ser, address)
                frame = meterbus.load(
                    meterbus.recv_frame(ser, meterbus.FRAME_DATA_LENGTH)
                )
            else:
                # Standard single-frame request
                meterbus.send_request_frame(ser, address)
                frame = meterbus.load(
                    meterbus.recv_frame(ser, meterbus.FRAME_DATA_LENGTH)
                )

            # Check if response is a valid telegram
            if not isinstance(frame, meterbus.TelegramLong):
                return None

            if frame.body.bodyHeader.noDataHeader:
                _LOGGER.debug(
                    "No header data available from meter at address %s", address
                )
                return None

            # Handle multi-frame accumulation if requested
            if multi:
                frame_count = 1
                while (
                    hasattr(frame, "more_records_follow")
                    and frame.more_records_follow
                    and frame_count < MAX_FRAMES
                ):
                    # Toggle FCB bit for next request
                    req.header.cField.parts[0] ^= meterbus.CONTROL_MASK_FCB

                    # Send toggled request
                    req = meterbus.send_request_frame_multi(ser, address, req)

                    # Receive next frame
                    next_frame = meterbus.load(
                        meterbus.recv_frame(ser, meterbus.FRAME_DATA_LENGTH)
                    )

                    # Accumulate frames
                    frame += next_frame
                    frame_count += 1

                # Log warning if frame limit reached
                if frame_count >= MAX_FRAMES:
                    _LOGGER.warning(
                        "Frame limit reached for address %d - possible meter bug",
                        address,
                    )

                _LOGGER.debug("Received %d frames from address %d", frame_count, address)

            # Extract header data
            interpreted_bodyHeader = frame.body.bodyHeader.interpreted

            meter_data = {
                MBUS_KEY_MANUFACTURER: interpreted_bodyHeader["manufacturer"],
                MBUS_KEY_IDENTIFICATION: re.sub(
                    r"0x|,| ", "", interpreted_bodyHeader["identification"]
                ),
                MBUS_KEY_VERSION: int(interpreted_bodyHeader["version"], 16),
                MBUS_KEY_MEDIUM: int(interpreted_bodyHeader["medium"], 16),
                MBUS_KEY_RECORDS: {},
            }

            # Process records if requested
            if records:
                record: meterbus.TelegramVariableDataRecord
                for record in frame.records:
                    interpreted_record = record.interpreted

                    meter_data[MBUS_KEY_RECORDS][
                        f"{interpreted_record['storage_number']}_{interpreted_record['type']}_{interpreted_record['unit']}_{interpreted_record['function']}"
                    ] = {
                        "value": interpreted_record["value"],
                        "unit": interpreted_record["unit"],
                        "type": interpreted_record["type"],
                        "storage_number": interpreted_record["storage_number"],
                        "function": interpreted_record["function"],
                    }

        except (meterbus.MBusFrameDecodeError, serial.SerialException, OSError) as err:
            _LOGGER.debug("No data from meter at address %s: %s", address, err)
            return None
        except Exception as err:  # noqa: BLE001
            # Catch any other timeout or communication errors in executor task
            _LOGGER.debug(
                "Timeout or error querying meter at address %s: %s", address, err
            )
            return None
        else:
            _LOGGER.debug(meter_data)
            return meter_data
