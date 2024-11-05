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
from lsst.ts import utils
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
from ..utils import (
    FREQUENCY_OID_LIST,
    RARITAN_EXT_SENS_DEC_DIGITS_IDS,
    DeviceName,
    RaritanItemId,
    RaritanOid,
    TelemetryItemName,
    TelemetryItemType,
)
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

        # Some SNMP devices emit a LOT of telemetry. Therefore the code loops
        # over one of more ObjectType instances to limit the amount of
        # telemetry items that get queried.
        self.object_types = [
            ObjectType(ObjectIdentity(self.mib_tree_holder.mib_tree["system"].oid))
        ]

        # Keep track of the nextCmd function so we can override it when in
        # simulation mode.
        self.next_cmd = nextCmd

        # Attributes for telemetry processing.
        self.snmp_result: dict[str, str] = {}
        self.system_description = "No system description set."
        self.raritan_decimal_digits: dict[str, int | list[int]] = {}

    @classmethod
    def get_config_schema(cls) -> dict[str, typing.Any]:
        """Get the config schema as jsonschema dict."""
        return yaml.safe_load(
            f"""
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
    - {DeviceName.netbooter.value}
    - {DeviceName.raritan.value}
    - {DeviceName.schneiderPm5xxx.value}
    - {DeviceName.xups.value}
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

        await self.execute_next_cmd_non_blocking()

        # Only the sysDescr value is expected at this moment.
        sys_descr = self.mib_tree_holder.mib_tree["sysDescr"].oid + ".0"
        if sys_descr in self.snmp_result:
            self.system_description = self.snmp_result[sys_descr]
        else:
            self.log.error("Could not retrieve sysDescr. Continuing.")

        if self.device_type == DeviceName.raritan.value:
            await self._get_raritan_decimal_digits()

    async def _get_raritan_decimal_digits(self) -> None:
        """Helper method to get the Raritan decimal digits.

        The decimal digits are needed to convert ints to floats by dividing the
        int by 10**decimal_digit.

        The Raritan decimal digits are fixed. Querying once when this class
        gets initialized helps to process the telemetry later without the need
        to query these fixed values repeatedly.
        """
        self.object_types = [
            ObjectType(ObjectIdentity(raritan_oid))
            for raritan_oid in [
                roid.value for roid in RaritanOid if "DecimalDigits" in roid.name
            ]
        ]
        await self.execute_next_cmd_non_blocking()

        # The snmp_result contains the number of decimal digits for each inlet
        # and each outlet telemetry item.
        for snmp_result_oid in self.snmp_result:
            item_id = int(snmp_result_oid.split(".")[-1])

            if snmp_result_oid.startswith(RaritanOid.ExternalSensorDecimalDigits.value):
                # The numbering of the externsl sensor items differs from the
                # numbering of the other items so some additional code is
                # needed.
                await self._get_raritan_external_sensor_decimal_digits(
                    snmp_result_oid, item_id
                )
            else:
                # The rest of the items use the same nunbering.
                await self._get_raritan_misc_decimal_digits(snmp_result_oid, item_id)

    async def _get_raritan_external_sensor_decimal_digits(
        self, result: str, item_id: int
    ) -> None:
        """Helper method to get the Raritan decimal digits for external
        sensors."""
        # Each external sensor item has 2 values so a list is needed.
        item_name = RARITAN_EXT_SENS_DEC_DIGITS_IDS[f"{item_id}"]
        if item_name not in self.raritan_decimal_digits:
            self.raritan_decimal_digits[item_name] = []
        decimal_digits = self.raritan_decimal_digits[item_name]
        assert isinstance(decimal_digits, list)
        decimal_digits.append(int(self.snmp_result[result]))

    async def _get_raritan_misc_decimal_digits(self, result: str, item_id: int) -> None:
        """Helper method to get the Raritan decimal digits for anything but
        external sensors."""
        item_name = RaritanItemId(item_id).name
        raritan_item = f"{item_name[0].upper()}{item_name[1:]}"
        if result.startswith(RaritanOid.InletDecimalDigits.value):
            # Each inlet item only has one value.
            self.raritan_decimal_digits[f"inlet{raritan_item}"] = int(
                self.snmp_result[result]
            )
        elif result.startswith(RaritanOid.OutletDecimalDigits.value):
            # Each outlet item has 48 values so a list is needed.
            raritan_item = f"outlet{raritan_item}"
            if raritan_item not in self.raritan_decimal_digits:
                self.raritan_decimal_digits[raritan_item] = []
            decimal_digits = self.raritan_decimal_digits[raritan_item]
            assert isinstance(decimal_digits, list)
            decimal_digits.append(int(self.snmp_result[result]))
        else:
            self.log.error(f"Obtained result for unknown decimal digit OID {result}.")

    async def read_data(self) -> None:
        """Read data from the SNMP server."""
        # Create the ObjectType(s) for the particular SNMP device type.
        if self.device_type in self.mib_tree_holder.mib_tree:
            if self.device_type == DeviceName.raritan.value:
                # Here we only are interested in the Raritan Telemetry OIDs
                # since the decimal digits were queried in `setup_reading`.
                self.object_types = [
                    ObjectType(ObjectIdentity(raritan_oid))
                    for raritan_oid in [
                        roid.value for roid in RaritanOid if "Telemetry" in roid.name
                    ]
                ]
            else:
                self.object_types = [
                    ObjectType(
                        ObjectIdentity(
                            self.mib_tree_holder.mib_tree[self.device_type].oid
                        )
                    )
                ]
        else:
            raise ValueError(f"Unknown device type {self.device_type!r}. Ignoring.")

        await self.execute_next_cmd_non_blocking()

        telemetry_topic = getattr(self.topics, f"tel_{self.device_type}")
        telemetry_dict: dict[str, typing.Any] = {
            "systemDescription": self.system_description,
            "sensorName": self.config.host,
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
                or i == "sensorName"
            )
        ]

        if self.device_type == DeviceName.raritan.value:
            # Raritan MIB files are very generic. The misc code will not work
            # with Raritan telemetry. Therefore a dedicated method is needed.
            await self.process_telemetry_item_for_raritan_device(telemetry_dict)
        else:
            for telemetry_item in telemetry_items:
                await self.process_telemetry_item_for_misc_device(
                    telemetry_item, telemetry_dict, telemetry_topic
                )

        await telemetry_topic.set_write(**telemetry_dict)
        await asyncio.sleep(self.config.poll_interval)

    async def process_telemetry_item_for_misc_device(
        self,
        telemetry_item: str,
        telemetry_dict: dict[str, typing.Any],
        telemetry_topic: salobj.topics.WriteTopic | types.SimpleNamespace,
    ) -> None:
        """Generic method to process the value of the provided telemetry item
        and add it to the provided dictionary.

        This method is called if there is no device specific method.

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

    async def process_telemetry_item_for_raritan_device(
        self, telemetry_dict: dict[str, typing.Any]
    ) -> None:
        """Process the SNMP telemetry of a Raritan device.

        Raritan devices have a very generic MIB file and a configurable amount
        of array values for most of their telemetry. Therefore a dedicated
        method is required to process that telemetry correctly.

        Parameters
        ----------
        telemetry_dict : `dict`[`str`, `typing.Any`]
            A dictionary that will contain all telemetry items and their
            values.
        """

        await self._process_raritan_inlet_telemetry(telemetry_dict)
        await self._process_raritan_outlet_telemetry(telemetry_dict)
        await self._process_raritan_external_sensor_telemetry()

    async def _process_raritan_inlet_telemetry(
        self, telemetry_dict: dict[str, typing.Any]
    ) -> None:
        """Process the SNMP telemetry of a Raritan inlet."""
        for snmp_result_oid in self.snmp_result:
            if snmp_result_oid.startswith(RaritanOid.InletTelemetry):
                item_id = int(snmp_result_oid.split(".")[-1])
                item_name = RaritanItemId(item_id).name
                raritan_item = f"inlet{item_name[0].upper()}{item_name[1:]}"
                decimal_digits = self.raritan_decimal_digits[raritan_item]
                assert isinstance(decimal_digits, int)
                telemetry_dict[raritan_item] = (
                    int(self.snmp_result[snmp_result_oid]) / 10**decimal_digits
                )

    async def _process_raritan_outlet_telemetry(
        self, telemetry_dict: dict[str, typing.Any]
    ) -> None:
        """Process the SNMP telemetry of Raritan outlets."""
        for snmp_result_oid in self.snmp_result:
            if snmp_result_oid.startswith(RaritanOid.OutletTelemetry):
                item_indices = snmp_result_oid.split(".")
                item_id = int(item_indices[-1])
                item_index = int(item_indices[-2])
                item_name = RaritanItemId(item_id).name
                raritan_item = f"outlet{item_name[0].upper()}{item_name[1:]}"
                all_decimal_digits = self.raritan_decimal_digits[raritan_item]
                assert isinstance(all_decimal_digits, list)
                decimal_digits = all_decimal_digits[item_index - 1]
                if raritan_item not in telemetry_dict:
                    telemetry_dict[raritan_item] = []
                telemetry_item = telemetry_dict[raritan_item]
                assert isinstance(telemetry_item, list)
                telemetry_dict[raritan_item].append(
                    int(self.snmp_result[snmp_result_oid]) / 10**decimal_digits
                )

    async def _process_raritan_external_sensor_telemetry(self) -> None:
        """Process the SNMP telemetry of Raritan external sensors."""

        # Each Raritan device has two temperature and two humidity sensors.
        temp_index = 0
        temperatures = [math.nan] * 2
        rel_hum_idex = 0
        relative_humidities = [math.nan] * 2

        for snmp_result_oid in self.snmp_result:
            if snmp_result_oid.startswith(RaritanOid.ExternalSensorTelemetry):
                item_id = int(snmp_result_oid.split(".")[-1])
                item_name = RARITAN_EXT_SENS_DEC_DIGITS_IDS[f"{item_id}"]
                decimal_digits = self.raritan_decimal_digits[item_name]
                assert isinstance(decimal_digits, list)
                if item_name == RaritanItemId.temperature.name:
                    temperatures[temp_index] = (
                        int(self.snmp_result[snmp_result_oid])
                        / 10 ** decimal_digits[temp_index]
                    )
                    temp_index += 1
                elif item_name == RaritanItemId.humidity.name:
                    relative_humidities[rel_hum_idex] = (
                        int(self.snmp_result[snmp_result_oid])
                        / 10 ** decimal_digits[rel_hum_idex]
                    )
                    rel_hum_idex += 1

        nelts = len(self.topics.tel_temperature.DataType().temperatureItem)
        temperature_array = temperatures + [math.nan] * (nelts - 2)
        timestamp = utils.current_tai()
        await self.topics.tel_temperature.set_write(
            sensorName=self.config.host,
            timestamp=timestamp,
            temperatureItem=temperature_array,
            numChannels=2,
            location="temperature1, temperature2",
        )

        for index, relative_humidity in enumerate(relative_humidities):
            await self.topics.tel_relativeHumidity.set_write(
                sensorName=self.config.host,
                timestamp=timestamp,
                relativeHumidityItem=relative_humidity,
                location=f"relativeHumidity{index}",
            )

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

    async def execute_next_cmd_non_blocking(self) -> None:
        """Call the blocking `execute_next_cmd` method from within the async
        loop."""
        self.snmp_result = {}
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            await loop.run_in_executor(pool, self.execute_next_cmd)

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
        for object_type in self.object_types:
            iterator = self.next_cmd(
                self.snmp_engine,
                self.community_data,
                self.transport_target,
                self.context_data,
                object_type,
                lookupMib=False,
                lexicographicMode=False,
            )

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
