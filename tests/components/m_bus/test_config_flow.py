"""Test the M-Bus config flow."""

from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.components.m_bus.const import (
    CONF_MBUS_SERIAL_PROTOCOL,
    DOMAIN,
    MBUS_SERIAL_PROTOCOL_SOCKET,
)
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry


async def test_form(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.m_bus.config_flow.MBusMasterConfigFlowHandler._test_connection"
    ) as mock_test_connection:
        mock_test_connection.return_value = None
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 10001,
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "socket://192.168.1.100:10001"
    assert result["data"] == {
        CONF_MBUS_SERIAL_PROTOCOL: MBUS_SERIAL_PROTOCOL_SOCKET,
        CONF_HOST: "192.168.1.100",
        CONF_PORT: 10001,
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_duplicate_entry(hass: HomeAssistant) -> None:
    """Test duplicate entries are handled properly."""
    # Create first entry
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_MBUS_SERIAL_PROTOCOL: MBUS_SERIAL_PROTOCOL_SOCKET,
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 10001,
        },
    )
    config_entry.add_to_hass(hass)

    # Try to create duplicate
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.m_bus.config_flow.MBusMasterConfigFlowHandler._test_connection"
    ) as mock_test_connection:
        mock_test_connection.return_value = None
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 10001,
            },
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_form_connection_test_fails(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test connection test failure shows error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    from homeassistant.components.m_bus.config_flow import CannotConnect
    
    with patch(
        "homeassistant.components.m_bus.config_flow.MBusMasterConfigFlowHandler._test_connection"
    ) as mock_test_connection:
        mock_test_connection.side_effect = CannotConnect()

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 10001,
            },
        )

    # Should show error on same form with retained input
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}

    # Test that we can successfully configure after fixing the connection
    with patch(
        "homeassistant.components.m_bus.config_flow.MBusMasterConfigFlowHandler._test_connection"
    ) as mock_test_connection:
        mock_test_connection.return_value = None  # Connection now works

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 10001,
            },
        )

    # Should now succeed
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "socket://192.168.1.100:10001"


async def test_reconfigure_flow(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test reconfiguration of host and port."""
    # Create existing entry
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_MBUS_SERIAL_PROTOCOL: MBUS_SERIAL_PROTOCOL_SOCKET,
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 10001,
        },
        title="Original Gateway",
    )
    config_entry.add_to_hass(hass)

    # Start reconfiguration flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "reconfigure", "entry_id": config_entry.entry_id},
    )

    # Should show reconfiguration form with current values
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["description_placeholders"] == {"name": "Original Gateway"}

    # Submit new configuration
    with patch(
        "homeassistant.components.m_bus.config_flow.MBusMasterConfigFlowHandler._test_connection"
    ) as mock_test_connection:
        mock_test_connection.return_value = None

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.200",
                CONF_PORT: 10002,
            },
        )

    # Should update and reload the entry
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    # Verify the entry was updated
    assert config_entry.data[CONF_HOST] == "192.168.1.200"
    assert config_entry.data[CONF_PORT] == 10002
