# This file is part of ts_ess_common.
#
# Developed for the Vera Rubin Observatory Telescope and Site Systems.
# This product includes software developed by the Vera Rubin Observatory
# Project (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations

__all__ = ["SnmpDataClient"]

import asyncio
import concurrent
import logging
import math
import re
import types
import typing

import yaml
from pysnmp.hlapi import (
    CommunityData,
    ContextData,
    ObjectIdentity,
    ObjectType,
    SnmpEngine,
    UdpTransportTarget,
    nextCmd,
)

from ..mib_tree_holder import MibTreeHolder
from ..snmp_server_simulator import SnmpServerSimulator
from ..utils import FREQUENCY_OID_LIST, TelemetryItemName, TelemetryItemType
from .base_read_loop_data_client import BaseReadLoopDataClient

if typing.TYPE_CHECKING:
    from lsst.ts import salobj

hex_const_pattern = r"([a-zA-Z0-9]*)"
hx = re.compile(hex_const_pattern)
numeric_const_pattern = (
    r"[-+]? (?: (?: \d* \. \d+ ) | (?: \d+ \.? ) )(?: [Ee] [+-]? \d+ ) ?"
)
rx = re.compile(numeric_const_pattern, re.VERBOSE)


class SnmpDataClient(BaseReadLoopDataClient):
    """Read SNMP data from a server and publish it as ESS telemetry.

    SNMP stands for Simple Network Management Protocol.

    Parameters
    ----------
    config : `types.SimpleNamespace`
        The configuration, after validation by the schema returned
        by `get_config_schema` and conversion to a types.SimpleNamespace.
    topics : `salobj.Controller`
        The telemetry topics this model can write, as a struct with attributes
        such as ``tel_temperature``.
    log : `logging.Logger`
        Logger.
    simulation_mode : `int`, optional
        Simulation mode; 0 for normal operation.

    Notes
    -----
    The config is required to contain "max_read_timeouts". If it doesn't, a
    RuntimeError is raised at instantiation.
    """

    def __init__(
        self,
        config: types.SimpleNamespace,
        topics: salobj.Controller | types.SimpleNamespace,
        log: logging.Logger,
        simulation_mode: int = 0,
    ) -> None:
        super().__init__(
            config=config,
            topics=topics,
            log=log,
            simulation_mode=simulation_mode,
        )

        # TODO DM-46349 Remove backward compatibility with XML 22.1.
        if not hasattr(topics, f"tel_{self.config.device_type}"):
            raise RuntimeError(
                f"Telemetry for {self.config.device_type} not supported."
            )

        self.mib_tree_holder = MibTreeHolder()

        self.device_type = self.config.device_type

        # Attributes for the SNMP requests.
        self.snmp_engine = SnmpEngine()
        self.community_data = CommunityData(self.config.snmp_community, mpModel=0)
        self.transport_target = UdpTransportTarget((self.config.host, self.config.port))
        self.context_data = ContextData()
        self.object_type = ObjectType(
            ObjectIdentity(self.mib_tree_holder.mib_tree["system"].oid)
        )

        # Keep track of the nextCmd function so we can override it when in
        # simulation mode.
        self.next_cmd = nextCmd

        # Attributes for telemetry processing.
        self.snmp_result: dict[str, str] = {}
        self.system_description = "No system description set."

    @classmethod
    def get_config_schema(cls) -> dict[str, typing.Any]:
        """Get the config schema as jsonschema dict."""
        return yaml.safe_load(
            """
$schema: http://json-schema.org/draft-07/schema#
description: Schema for SnmpDataClient.
type: object
properties:
  host:
    description: Host name of the TCP/IP interface.
    type: string
    format: hostname
  port:
    description: Port number of the TCP/IP interface. Defaults to the SNMP port.
    type: integer
    default: 161
  max_read_timeouts:
    description: Maximum number of read timeouts before an exception is raised.
    type: integer
    default: 5
  device_name:
    description: The name of the device.
    type: string
  device_type:
    description: The type of device.
    type: string
    enum:
    - pdu
    - schneiderPm5xxx
    - xups
  snmp_community:
    description: The SNMP community.
    type: string
    default: public
  poll_interval:
    description: The amount of time [s] between each telemetry poll.
    type: number
    default: 1.0
required:
  - host
  - port
  - max_read_timeouts
  - device_name
  - device_type
  - poll_interval
additionalProperties: false
"""
        )

    def descr(self) -> str:
        """Return a brief description, without the class name.

        This should be just enough information to distinguish
        one instance of this client from another.
        """
        return f"[host={self.config.host}, port={self.config.port}]"

    async def setup_reading(self) -> None:
        """Perform any tasks before starting the read loop.

        In this case the system description is retrieved and stored in memory,
        since this is not expected to change.
        """
        if self.simulation_mode == 1:
            snmp_server_simulator = SnmpServerSimulator(log=self.log)
            self.next_cmd = snmp_server_simulator.snmp_cmd

        # Call the blocking `execute_next_cmd` method from within the async
        # loop.
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            await loop.run_in_executor(pool, self.execute_next_cmd)

        # Only the sysDescr value is expected at this moment.
        sys_descr = self.mib_tree_holder.mib_tree["sysDescr"].oid + ".0"
        if sys_descr in self.snmp_result:
            self.system_description = self.snmp_result[sys_descr]
        else:
            self.log.error("Could not retrieve sysDescr. Continuing.")

        # Create the ObjectType for the particular SNMP device type.
        if self.device_type in self.mib_tree_holder.mib_tree:
            self.object_type = ObjectType(
                ObjectIdentity(self.mib_tree_holder.mib_tree[self.device_type].oid)
            )
        else:
            raise ValueError(
                f"Unknown device type {self.device_type!r}. "
                "Continuing querying only for 'sysDescr'."
            )

    async def read_data(self) -> None:
        """Read data from the SNMP server."""
        # Call the blocking `execute_next_cmd` method from within the async
        # loop.
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            await loop.run_in_executor(pool, self.execute_next_cmd)

        telemetry_topic = getattr(self.topics, f"tel_{self.device_type}")
        telemetry_dict: dict[str, typing.Any] = {
            "systemDescription": self.system_description
        }

        # Make the code work with both the DDS and Kafka versions of ts_salobj.
        if hasattr(telemetry_topic, "metadata"):
            fields = telemetry_topic.metadata.field_info
        elif hasattr(telemetry_topic, "topic_info"):
            fields = telemetry_topic.topic_info.fields
        else:
            fields = {}

        telemetry_items = [
            i
            for i in fields
            if not (
                i.startswith("private_")
                or i.startswith("_")
                or i == "salIndex"
                or i == "systemDescription"
            )
        ]

        for telemetry_item in telemetry_items:
            await self.process_telemetry_item(
                telemetry_item, telemetry_dict, telemetry_topic
            )

        await telemetry_topic.set_write(**telemetry_dict)
        await asyncio.sleep(self.config.poll_interval)

    async def process_telemetry_item(
        self,
        telemetry_item: str,
        telemetry_dict: dict[str, typing.Any],
        telemetry_topic: salobj.topics.WriteTopic | types.SimpleNamespace,
    ) -> None:
        """Process the value of the provided telemetry item and add it to the
        provided dictionary.

        Parameters
        ----------
        telemetry_item : `str`
            The name of ghe telemetry item.
        telemetry_dict : `dict`[`str`, `typing.Any`]
            A dictionary that will contain all telemetry items and their
            values.
        telemetry_topic : `WriteTopic` | `types.SimpleNameSpace`
            The telemetry topic containing the telemetry item.
        """
        mib_name = TelemetryItemName(telemetry_item).name
        parent = self.mib_tree_holder.mib_tree[mib_name].parent
        assert parent is not None

        snmp_value: typing.Any
        if parent.index and await self._is_single_or_multiple(
            telemetry_item, telemetry_topic
        ):
            mib_oid = self.mib_tree_holder.mib_tree[mib_name].oid
            snmp_value = []
            for snmp_result_oid in self.snmp_result:
                if snmp_result_oid.startswith(mib_oid):
                    snmp_value.append(
                        await self.get_telemetry_item_value(
                            telemetry_item, mib_name, snmp_result_oid
                        )
                    )
        else:
            if self.mib_tree_holder.mib_tree[mib_name].oid + ".0" in self.snmp_result:
                mib_oid = self.mib_tree_holder.mib_tree[mib_name].oid + ".0"
            else:
                mib_oid = self.mib_tree_holder.mib_tree[mib_name].oid + ".1"
            snmp_value = await self.get_telemetry_item_value(
                telemetry_item, mib_name, mib_oid
            )

            # Some frequencies are given in tens of Hertz.
            if mib_oid in FREQUENCY_OID_LIST:
                snmp_value = snmp_value / 10.0

        telemetry_dict[telemetry_item] = snmp_value

    async def _is_single_or_multiple(
        self,
        telemetry_item: str,
        telemetry_topic: salobj.topics.WriteTopic | types.SimpleNamespace,
    ) -> bool:
        """Determine if a telemetry item has a single or multiple value.

        Parameters
        ----------
        telemetry_item : `str`
            The name of ghe telemetry item.
        telemetry_topic : `WriteTopic` | `types.SimpleNameSpace`
            The telemetry topic containing the telemetry item.

        Returns
        -------
        bool
            False if single and True if multiple.
        """
        # Make the code work with both the DDS and Kafka versions of ts_salobj.
        if hasattr(telemetry_topic, "metadata"):
            field_info = telemetry_topic.metadata.field_info[telemetry_item]
            if hasattr(field_info, "count"):
                is_list = telemetry_topic.metadata.field_info[telemetry_item].count > 1
            else:
                is_list = (
                    telemetry_topic.metadata.field_info[telemetry_item].array_length
                    is not None
                )
        elif hasattr(telemetry_topic, "topic_info"):
            is_list = telemetry_topic.topic_info.fields[telemetry_item].count > 1
        else:
            is_list = False
        return is_list

    async def get_telemetry_item_value(
        self, telemetry_item: str, mib_name: str, mib_oid: str
    ) -> typing.Any:
        """Get the value of a telemetry item.

        Parameters
        ----------
        telemetry_item : `str`
            The name of the telemetry item.
        mib_name : `str`
            The MIB name of the item.
        mib_oid : `str`
            The MIB OID of the item.

        Returns
        -------
        int | float | str
            The value of the item.

        Raises
        ------
        ValueError
            In case no float value could be gotten.
        """
        telemetry_type = TelemetryItemType[mib_name]
        snmp_value: int | float | str
        match telemetry_type:
            case "int":
                if mib_oid in self.snmp_result:
                    snmp_value = int(self.snmp_result[mib_oid])
                else:
                    snmp_value = 0
                    self.log.debug(
                        f"Could not find {mib_oid=} for int {telemetry_item=}. "
                        "Ignoring."
                    )
            case "float":
                if mib_oid in self.snmp_result:
                    snmp_value = await self._extract_float_from_string(
                        self.snmp_result[mib_oid]
                    )
                else:
                    snmp_value = math.nan
                    self.log.debug(
                        f"Could not find {mib_oid=} for float {telemetry_item=}. "
                        "Ignoring."
                    )
            case "string":
                if mib_oid in self.snmp_result:
                    snmp_value = self.snmp_result[mib_oid]
                else:
                    snmp_value = ""
                    self.log.debug(
                        f"Could not find {mib_oid=} for str {telemetry_item=}. "
                        "Ignoring."
                    )
            case _:
                snmp_value = self.snmp_result[mib_oid]
        return snmp_value

    async def _extract_float_from_string(self, float_string: str) -> float:
        """Extract a float value from a string.

        It is assumed here that there only is a single float value in the
        string. If no or more than one float value is found, a ValueError is
        raised.

        Parameters
        ----------
        float_string : `str`
            The string containing the float value.

        Raises
        ------
        ValueError
            In case no single float value could be extracted from the string.
        """
        try:
            float_value = float(float_string)
        except ValueError as e:
            # Some values are passed on as hex strings.
            if float_string.startswith("0x"):
                float_string = float_string[2:]
                hex_values = hx.findall(float_string)
                if len(hex_values) > 0:
                    float_value_as_bytes = bytes.fromhex(hex_values[0])
                    float_string = float_value_as_bytes.decode("utf-8")
            float_values = rx.findall(float_string)
            if len(float_values) > 0:
                float_value = float(float_values[0])
            else:
                raise e
        return float_value

    def execute_next_cmd(self) -> None:
        """Execute the SNMP nextCmd command.

        This is a **blocking** method that needs to be called with the asyncio
        `run_in_executor` method.

        Raises
        ------
        RuntimeError
            In case an SNMP error happens, for instance the server cannot be
            reached.
        """
        iterator = self.next_cmd(
            self.snmp_engine,
            self.community_data,
            self.transport_target,
            self.context_data,
            self.object_type,
            lookupMib=False,
            lexicographicMode=False,
        )

        self.snmp_result = {}
        for error_indication, error_status, error_index, var_binds in iterator:
            if error_indication:
                self.log.warning(
                    f"Exception contacting SNMP server with {error_indication=}. Ignoring."
                )
            elif error_status:
                self.log.exception(
                    "Exception contacting SNMP server with "
                    f"{error_status.prettyPrint()} at "
                    f"{error_index and var_binds[int(error_index) - 1][0] or '?'}. Ignoring."
                )
            else:
                for var_bind in var_binds:
                    self.snmp_result[var_bind[0].prettyPrint()] = var_bind[
                        1
                    ].prettyPrint()
