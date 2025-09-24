"""Constants for the M-Bus integration."""

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfMass,
    UnitOfPower,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolume,
    UnitOfVolumeFlowRate,
)

DOMAIN = "m_bus"

CONF_MBUS_SERIAL_PROTOCOL = "mbus_serial_protocol"

MBUS_SERIAL_PROTOCOL_SOCKET = "socket"

# Default values
MBUS_DEFAULT_SOCKET_PORT = 10001

# M-Bus Medium Field Codes - based on EN 13757-3 standard
MBUS_MEDIUM_TYPES = {
    0x00: "Other",
    0x01: "Oil",
    0x02: "Electricity",
    0x03: "Gas",
    0x04: "Heat (Outgoing)",
    0x05: "Steam",
    0x06: "Hot Water",
    0x07: "Water",
    0x08: "Heat Cost",
    0x09: "Compressed Air",
    0x0A: "Cooling (Outgoing)",
    0x0B: "Cooling (Incoming)",
    0x0C: "Heat (Incoming)",
    0x0D: "Heat/Cooling",
    0x0E: "Bus",
    0x0F: "Unknown",
    0x10: "Irrigation",
    0x11: "Water Logger",
    0x12: "Gas Logger",
    0x13: "Gas Converter",
    0x14: "Calorific",
    0x15: "Boiler Water",
    0x16: "Cold Water",
    0x17: "Dual Water",
    0x18: "Pressure",
    0x19: "ADC",
    0x1A: "Smoke",
    0x1B: "Room Sensor",
    0x1C: "Gas Detector",
    0x20: "Electrical Breaker",
    0x21: "Valve",
    0x25: "Customer Unit",
    0x28: "Waste Water",
    0x29: "Garbage",
    0x30: "Service Unit",
    0x36: "RC System",
    0x37: "RC Meter",
}

# M-Bus meter data field keys
MBUS_KEY_ADDRESS = "address"
MBUS_KEY_MANUFACTURER = "manufacturer"
MBUS_KEY_IDENTIFICATION = "identification"
MBUS_KEY_VERSION = "version"
MBUS_KEY_MEDIUM = "medium"
MBUS_KEY_RECORDS = "records"

# M-Bus unit conversion lookup table
# Maps meterbus MeasureUnit enum strings to Home Assistant unit constants
MBUS_UNIT_LOOKUP = {
    # Temperature
    "MeasureUnit.C": UnitOfTemperature.CELSIUS,
    "MeasureUnit.K": UnitOfTemperature.KELVIN,

    # Energy
    "MeasureUnit.WH": UnitOfEnergy.WATT_HOUR,
    "MeasureUnit.KWH": UnitOfEnergy.KILO_WATT_HOUR,
    "MeasureUnit.J": UnitOfEnergy.JOULE,

    # Power
    "MeasureUnit.W": UnitOfPower.WATT,
    "MeasureUnit.J_H": "J/h",  # Custom unit - no HA equivalent

    # Volume
    "MeasureUnit.M3": UnitOfVolume.CUBIC_METERS,
    "MeasureUnit.L": UnitOfVolume.LITERS,

    # Volume Flow Rate
    "MeasureUnit.M3_H": UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
    "MeasureUnit.M3_MIN": UnitOfVolumeFlowRate.CUBIC_METERS_PER_MINUTE,
    "MeasureUnit.M3_S": UnitOfVolumeFlowRate.CUBIC_METERS_PER_SECOND,

    # Mass
    "MeasureUnit.KG": UnitOfMass.KILOGRAMS,
    "MeasureUnit.KG_H": "kg/h",  # Custom unit - no HA equivalent

    # Pressure
    "MeasureUnit.BAR": UnitOfPressure.BAR,

    # Electrical
    "MeasureUnit.V": UnitOfElectricPotential.VOLT,
    "MeasureUnit.A": UnitOfElectricCurrent.AMPERE,

    # Time
    "MeasureUnit.SECONDS": UnitOfTime.SECONDS,
    "MeasureUnit.MINUTES": UnitOfTime.MINUTES,
    "MeasureUnit.HOURS": UnitOfTime.HOURS,
    "MeasureUnit.DAYS": UnitOfTime.DAYS,

    # Percentage
    "MeasureUnit.PERCENT": PERCENTAGE,

    # Special/Other units
    "MeasureUnit.HCA": "H.C.A",  # Heat Cost Allocator units
    "MeasureUnit.CURRENCY": None,  # Currency - no generic HA unit
    "MeasureUnit.BAUD": "Baud",  # Communication baud rate
    "MeasureUnit.BIT_TIMES": "bittimes",  # Communication timing
    "MeasureUnit.DBM": "dBm",  # Signal strength

    # Date/Time - not applicable for numeric sensors
    "MeasureUnit.DATE": None,
    "MeasureUnit.TIME": None,
    "MeasureUnit.DATE_TIME": None,
    "MeasureUnit.DATE_TIME_S": None,

    # Dimensionless/None
    "MeasureUnit.NONE": None,
}

# M-Bus VIFUnit to SensorDeviceClass lookup table
# Maps meterbus VIFUnit enum strings to Home Assistant SensorDeviceClass values
MBUS_VIF_DEVICE_CLASS_LOOKUP = {
    # Energy
    "VIFUnit.ENERGY_WH": SensorDeviceClass.ENERGY,
    "VIFUnit.ENERGY_J": SensorDeviceClass.ENERGY,

    # Volume
    "VIFUnit.VOLUME": SensorDeviceClass.VOLUME,

    # Mass/Weight
    "VIFUnit.MASS": SensorDeviceClass.WEIGHT,

    # Time/Duration
    "VIFUnit.ON_TIME": SensorDeviceClass.DURATION,
    "VIFUnit.OPERATING_TIME": SensorDeviceClass.DURATION,
    "VIFUnit.AVG_DURATION": SensorDeviceClass.DURATION,
    "VIFUnit.ACTUALITY_DURATION": SensorDeviceClass.DURATION,

    # Power
    "VIFUnit.POWER_W": SensorDeviceClass.POWER,
    "VIFUnit.POWER_J_H": SensorDeviceClass.POWER,

    # Extended VIF units for electrical measurements
    "VIFUnitExt.VOLTS": SensorDeviceClass.VOLTAGE,
    "VIFUnitExt.AMPERE": SensorDeviceClass.CURRENT,

    # Volume Flow Rate
    "VIFUnit.VOLUME_FLOW": SensorDeviceClass.VOLUME_FLOW_RATE,
    "VIFUnit.VOLUME_FLOW_EXT": SensorDeviceClass.VOLUME_FLOW_RATE,
    "VIFUnit.VOLUME_FLOW_EXT_S": SensorDeviceClass.VOLUME_FLOW_RATE,
    "VIFUnit.MASS_FLOW": SensorDeviceClass.VOLUME_FLOW_RATE,  # Mass flow treated as flow rate

    # Temperature
    "VIFUnit.FLOW_TEMPERATURE": SensorDeviceClass.TEMPERATURE,
    "VIFUnit.RETURN_TEMPERATURE": SensorDeviceClass.TEMPERATURE,
    "VIFUnit.TEMPERATURE_DIFFERENCE": SensorDeviceClass.TEMPERATURE,
    "VIFUnit.EXTERNAL_TEMPERATURE": SensorDeviceClass.TEMPERATURE,

    # Pressure
    "VIFUnit.PRESSURE": SensorDeviceClass.PRESSURE,

    # Date/Time - non-numeric
    "VIFUnit.DATE": SensorDeviceClass.DATE,
    "VIFUnit.DATE_TIME": SensorDeviceClass.TIMESTAMP,
    "VIFUnit.DATE_TIME_GENERAL": SensorDeviceClass.TIMESTAMP,
    "VIFUnit.EXTENTED_TIME": SensorDeviceClass.TIMESTAMP,
    "VIFUnit.EXTENTED_DATE_TIME": SensorDeviceClass.TIMESTAMP,

    # Special/Other units - no specific device class
    "VIFUnit.UNITS_FOR_HCA": None,  # Heat Cost Allocator units
    "VIFUnit.FABRICATION_NO": None,  # Serial numbers
    "VIFUnit.IDENTIFICATION": None,  # Device identification
    "VIFUnit.ADDRESS": None,  # Bus addresses
    "VIFUnit.RES_THIRD_VIFE_TABLE": None,  # Reserved
    "VIFUnit.FIRST_EXT_VIF_CODES": None,  # Extension codes
    "VIFUnit.VARIABLE_VIF": None,  # Variable VIF
    "VIFUnit.VIF_FOLLOWING": None,  # VIF following
    "VIFUnit.SECOND_EXT_VIF_CODES": None,  # Extension codes
    "VIFUnit.THIRD_EXT_VIF_CODES_RES": None,  # Reserved extension codes
    "VIFUnit.ANY_VIF": None,  # Any VIF
    "VIFUnit.MANUFACTURER_SPEC": None,  # Manufacturer specific
}

# M-Bus State Class mapping based on VIF Unit and Function Type combination
# Maps (VIF_Unit_String, Function_String) tuples to SensorStateClass
MBUS_STATE_CLASS_LOOKUP = {
    # Energy measurements - always cumulative totals for instantaneous readings
    ("VIFUnit.ENERGY_WH", "Instantaneous value"): SensorStateClass.TOTAL_INCREASING,
    ("VIFUnit.ENERGY_J", "Instantaneous value"): SensorStateClass.TOTAL_INCREASING,

    # Volume measurements - always cumulative totals for instantaneous readings
    ("VIFUnit.VOLUME", "Instantaneous value"): SensorStateClass.TOTAL_INCREASING,

    # Mass measurements - cumulative totals for instantaneous readings
    ("VIFUnit.MASS", "Instantaneous value"): SensorStateClass.TOTAL_INCREASING,

    # Power measurements - instantaneous measurements
    ("VIFUnit.POWER_W", "Instantaneous value"): SensorStateClass.MEASUREMENT,
    ("VIFUnit.POWER_J_H", "Instantaneous value"): SensorStateClass.MEASUREMENT,

    # Flow rate measurements - instantaneous measurements
    ("VIFUnit.VOLUME_FLOW", "Instantaneous value"): SensorStateClass.MEASUREMENT,
    ("VIFUnit.VOLUME_FLOW_EXT", "Instantaneous value"): SensorStateClass.MEASUREMENT,
    ("VIFUnit.VOLUME_FLOW_EXT_S", "Instantaneous value"): SensorStateClass.MEASUREMENT,
    ("VIFUnit.MASS_FLOW", "Instantaneous value"): SensorStateClass.MEASUREMENT,

    # Temperature measurements - instantaneous measurements
    ("VIFUnit.FLOW_TEMPERATURE", "Instantaneous value"): SensorStateClass.MEASUREMENT,
    ("VIFUnit.RETURN_TEMPERATURE", "Instantaneous value"): SensorStateClass.MEASUREMENT,
    ("VIFUnit.TEMPERATURE_DIFFERENCE", "Instantaneous value"): SensorStateClass.MEASUREMENT,
    ("VIFUnit.EXTERNAL_TEMPERATURE", "Instantaneous value"): SensorStateClass.MEASUREMENT,

    # Pressure measurements - instantaneous measurements
    ("VIFUnit.PRESSURE", "Instantaneous value"): SensorStateClass.MEASUREMENT,

    # Extended VIF electrical measurements - instantaneous measurements
    ("VIFUnitExt.VOLTS", "Instantaneous value"): SensorStateClass.MEASUREMENT,
    ("VIFUnitExt.AMPERE", "Instantaneous value"): SensorStateClass.MEASUREMENT,

    # Time measurements - can be cumulative for operating hours
    ("VIFUnit.ON_TIME", "Instantaneous value"): SensorStateClass.TOTAL_INCREASING,
    ("VIFUnit.OPERATING_TIME", "Instantaneous value"): SensorStateClass.TOTAL_INCREASING,
    ("VIFUnit.AVG_DURATION", "Instantaneous value"): SensorStateClass.MEASUREMENT,
    ("VIFUnit.ACTUALITY_DURATION", "Instantaneous value"): SensorStateClass.MEASUREMENT,

    # Date/Time values - no state class (not numeric measurements)
    ("VIFUnit.DATE", "Instantaneous value"): None,
    ("VIFUnit.DATE_TIME", "Instantaneous value"): None,
    ("VIFUnit.DATE_TIME_GENERAL", "Instantaneous value"): None,
    ("VIFUnit.EXTENTED_TIME", "Instantaneous value"): None,
    ("VIFUnit.EXTENTED_DATE_TIME", "Instantaneous value"): None,

    # Special units - no state class
    ("VIFUnit.UNITS_FOR_HCA", "Instantaneous value"): None,  # Heat Cost Allocator
    ("VIFUnit.FABRICATION_NO", "Instantaneous value"): None,  # Serial numbers
    ("VIFUnit.IDENTIFICATION", "Instantaneous value"): None,  # Device IDs
    ("VIFUnit.ADDRESS", "Instantaneous value"): None,  # Bus addresses

    # All maximum/minimum/error values have no state class (diagnostic only)
    # These will be handled by pattern matching in the lookup function
}

# Function types that should never have state classes (diagnostic sensors)
MBUS_DIAGNOSTIC_FUNCTIONS = {
    "Maximum value",
    "Minimum value",
    "Error value",
    "Error state value",
}

# VIF units that represent cumulative values when function is "Instantaneous value"
MBUS_CUMULATIVE_VIF_UNITS = {
    "VIFUnit.ENERGY_WH",
    "VIFUnit.ENERGY_J",
    "VIFUnit.VOLUME",
    "VIFUnit.MASS",
    "VIFUnit.ON_TIME",
    "VIFUnit.OPERATING_TIME",
}

# VIF units that represent instantaneous measurements
MBUS_MEASUREMENT_VIF_UNITS = {
    "VIFUnit.POWER_W",
    "VIFUnit.POWER_J_H",
    "VIFUnit.VOLUME_FLOW",
    "VIFUnit.VOLUME_FLOW_EXT",
    "VIFUnit.VOLUME_FLOW_EXT_S",
    "VIFUnit.MASS_FLOW",
    "VIFUnit.FLOW_TEMPERATURE",
    "VIFUnit.RETURN_TEMPERATURE",
    "VIFUnit.TEMPERATURE_DIFFERENCE",
    "VIFUnit.EXTERNAL_TEMPERATURE",
    "VIFUnit.PRESSURE",
    "VIFUnit.AVG_DURATION",
    "VIFUnit.ACTUALITY_DURATION",
    # Extended VIF units
    "VIFUnitExt.VOLTS",
    "VIFUnitExt.AMPERE",
}


def get_mbus_state_class(record_type: str, record_function: str) -> SensorStateClass | None:
    """Determine the appropriate SensorStateClass for an M-Bus record.

    Args:
        record_type: The VIF unit type (e.g., "Energy", "Volume", "Power")
        record_function: The function type (e.g., "Instantaneous value", "Maximum value")

    Returns:
        SensorStateClass or None for diagnostic sensors
    """
    # Diagnostic functions never have state classes
    if record_function in MBUS_DIAGNOSTIC_FUNCTIONS:
        return None

    # Convert record type to VIF unit format for lookup
    vif_unit_key = f"VIFUnit.{record_type.upper().replace(' ', '_')}"
    lookup_key = (vif_unit_key, record_function)

    # Direct lookup first
    if lookup_key in MBUS_STATE_CLASS_LOOKUP:
        return MBUS_STATE_CLASS_LOOKUP[lookup_key]

    # Try VIFUnitExt lookup
    vif_unit_ext_key = f"VIFUnitExt.{record_type.upper().replace(' ', '_')}"
    lookup_key_ext = (vif_unit_ext_key, record_function)
    if lookup_key_ext in MBUS_STATE_CLASS_LOOKUP:
        return MBUS_STATE_CLASS_LOOKUP[lookup_key_ext]

    # Fallback logic for instantaneous values
    if record_function == "Instantaneous value":
        # Check if it's a cumulative type
        if vif_unit_key in MBUS_CUMULATIVE_VIF_UNITS:
            return SensorStateClass.TOTAL_INCREASING
        # Check if it's a measurement type
        if vif_unit_key in MBUS_MEASUREMENT_VIF_UNITS or vif_unit_ext_key in MBUS_MEASUREMENT_VIF_UNITS:
            return SensorStateClass.MEASUREMENT
        # Default for unknown instantaneous values
        return SensorStateClass.MEASUREMENT

    # No state class for non-instantaneous, non-diagnostic functions
    return None
