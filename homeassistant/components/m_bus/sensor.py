"""M-Bus sensor platform."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import MBusConfigEntry
from .const import (
    DOMAIN,
    MBUS_KEY_IDENTIFICATION,
    MBUS_KEY_MANUFACTURER,
    MBUS_KEY_MEDIUM,
    MBUS_KEY_RECORDS,
    MBUS_KEY_VERSION,
    MBUS_MEDIUM_TYPES,
    MBUS_UNIT_LOOKUP,
    MBUS_VIF_DEVICE_CLASS_LOOKUP,
    get_mbus_state_class,
)
from .coordinator import MBusCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: MBusConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up M-Bus sensor based on a config entry."""
    coordinator = config_entry.runtime_data

    # Create sensors from all discovered meters
    sensors: list[SensorEntity] = []
    for address, meter_data in coordinator.data.items():
        if meter_data is not None:
            sensors.extend(create_meter_sensors(coordinator, address, meter_data))

    async_add_entities(sensors)


def create_meter_sensors(
    coordinator: MBusCoordinator,
    address: int,
    meter_info: dict[str, Any],
) -> list[SensorEntity]:
    """Create sensors for a discovered meter."""
    sensors: list[SensorEntity] = []

    # Get meter records
    records = meter_info.get(MBUS_KEY_RECORDS, {})

    # Create a sensor for each record
    for record_key, record_data in records.items():
        sensor = MBusSensor(
            coordinator=coordinator,
            address=address,
            meter_info=meter_info,
            record_key=record_key,
            record_data=record_data,
        )
        sensors.append(sensor)

    return sensors


class MBusSensor(CoordinatorEntity[MBusCoordinator], SensorEntity):
    """M-Bus sensor entity."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: MBusCoordinator,
        address: int,
        meter_info: dict[str, Any],
        record_key: str,
        record_data: dict[str, Any],
    ) -> None:
        """Initialize M-Bus sensor."""
        super().__init__(coordinator)

        self._address = address
        self._meter_info = meter_info
        self._record_key = record_key
        self._record_data = record_data

        # Create unique ID based on meter identification and record key
        identification = meter_info[MBUS_KEY_IDENTIFICATION]
        self._attr_unique_id = f"{identification}_{record_key}"

        # Set up device info
        manufacturer = meter_info[MBUS_KEY_MANUFACTURER]
        medium_code = meter_info[MBUS_KEY_MEDIUM]
        medium_name = MBUS_MEDIUM_TYPES.get(medium_code, "Unknown")
        version = meter_info[MBUS_KEY_VERSION]

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, identification)},
            name=f"{manufacturer} {medium_name} Meter",
            manufacturer=manufacturer,
            model=f"{medium_name} Meter",
            sw_version=str(version),
        )

        # Set entity name based on record type and function
        record_type = record_data.get("type", "Unknown")
        record_function = record_data.get("function", "")
        storage_number = record_data.get("storage_number", 0)

        if record_function and record_function != "Instantaneous value":
            entity_name = f"{record_type} ({record_function})"
        else:
            entity_name = record_type

        if storage_number > 0:
            entity_name = f"{entity_name} {storage_number}"

        self._attr_name = entity_name

        # Set native unit of measurement
        unit_string = record_data.get("unit", "")
        self._attr_native_unit_of_measurement = MBUS_UNIT_LOOKUP.get(unit_string)

        # Set device class based on VIF unit type
        vif_unit_key = f"VIFUnit.{record_type.upper().replace(' ', '_')}"
        device_class = MBUS_VIF_DEVICE_CLASS_LOOKUP.get(vif_unit_key)
        if not device_class:
            vif_unit_ext_key = f"VIFUnitExt.{record_type.upper().replace(' ', '_')}"
            device_class = MBUS_VIF_DEVICE_CLASS_LOOKUP.get(vif_unit_ext_key)
        if device_class:
            self._attr_device_class = device_class

        # Set state class based on VIF unit type and function
        state_class = get_mbus_state_class(record_type, record_function)
        if state_class:
            self._attr_state_class = state_class

        # Set entity category for diagnostic sensors
        if record_function in ("Maximum value", "Minimum value", "Error value"):
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
            # Disable diagnostic sensors by default to reduce entity count
            self._attr_entity_registry_enabled_default = False

    @property
    def native_value(self) -> float | int | str | None:
        """Return the state of the sensor."""
        if self._address not in self.coordinator.data:
            return None

        meter_data = self.coordinator.data[self._address]
        if meter_data is None:
            return None

        records = meter_data.get(MBUS_KEY_RECORDS, {})
        record = records.get(self._record_key)

        if record is None:
            return None

        value = record.get("value")
        if value is None:
            return None

        # Handle different value types from M-Bus data
        # M-Bus can return numeric values, strings (for device IDs), or other types
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            # Try to convert string numbers to numeric values
            try:
                # Try integer first
                if "." not in value:
                    return int(value)
                return float(value)
            except (ValueError, TypeError):
                # Return as string for non-numeric values (device IDs, etc.)
                return value

        # For other types, try to convert or return as string
        try:
            return float(value)
        except (ValueError, TypeError):
            return str(value)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            super().available
            and self._address in self.coordinator.data
            and self.coordinator.data[self._address] is not None
        )
