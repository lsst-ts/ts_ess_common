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

__all__ = ["SnmpServerSimulator", "SIMULATED_SYS_DESCR"]

import logging
import random
import string
import typing

from pysnmp.hlapi import (
    CommunityData,
    ContextData,
    Integer,
    ObjectIdentity,
    ObjectType,
    SnmpEngine,
    UdpTransportTarget,
)
from pysnmp.proto.rfc1155 import ObjectName
from pysnmp.proto.rfc1902 import OctetString

from .mib_tree_holder import MibTreeHolder
from .utils import (
    FREQUENCY_OID_LIST,
    PDU_HEX_OID_LIST,
    SCHNEIDER_FLOAT_AS_STRING_OID_LIST,
    DeviceName,
    RaritanItemId,
    RaritanOid,
    TelemetryItemType,
)

SIMULATED_SYS_DESCR = "SnmpServerSimulator"

PDU_LIST_NUM_OIDS = 2
PDU_LIST_START_OID = 0
XUPS_LIST_NUM_OIDS = 3
XUPS_LIST_START_OID = 1
MISC_LIST_NUM_OIDS = 5
MISC_LIST_START_OID = 1

FIFTY_HZ_IN_TENS = 500

# Templates for the default values for the various Digital Digits Raritan OIDs.
RARITAN_INLET_DECIMAL_DIGITS = {
    "1.3.6.1.4.1.13742.6.3.3.4.1.7.1.{item_id}.1": 3,
    "1.3.6.1.4.1.13742.6.3.3.4.1.7.1.{item_id}.3": 0,
    "1.3.6.1.4.1.13742.6.3.3.4.1.7.1.{item_id}.4": 0,
    "1.3.6.1.4.1.13742.6.3.3.4.1.7.1.{item_id}.5": 0,
    "1.3.6.1.4.1.13742.6.3.3.4.1.7.1.{item_id}.6": 0,
    "1.3.6.1.4.1.13742.6.3.3.4.1.7.1.{item_id}.7": 2,
    "1.3.6.1.4.1.13742.6.3.3.4.1.7.1.{item_id}.8": 0,
    "1.3.6.1.4.1.13742.6.3.3.4.1.7.1.{item_id}.23": 1,
    "1.3.6.1.4.1.13742.6.3.3.4.1.7.1.{item_id}.60": 0,
    "1.3.6.1.4.1.13742.6.3.3.4.1.7.1.{item_id}.62": 0,
}
RARITAN_OUTLET_DECIMAL_DIGITS = {
    "1.3.6.1.4.1.13742.6.3.5.4.1.7.1.{item_id}.1": 3,
    "1.3.6.1.4.1.13742.6.3.5.4.1.7.1.{item_id}.4": 0,
    "1.3.6.1.4.1.13742.6.3.5.4.1.7.1.{item_id}.5": 0,
    "1.3.6.1.4.1.13742.6.3.5.4.1.7.1.{item_id}.6": 0,
    "1.3.6.1.4.1.13742.6.3.5.4.1.7.1.{item_id}.7": 2,
    "1.3.6.1.4.1.13742.6.3.5.4.1.7.1.{item_id}.8": 0,
    "1.3.6.1.4.1.13742.6.3.5.4.1.7.1.{item_id}.14": 0,
    "1.3.6.1.4.1.13742.6.3.5.4.1.7.1.{item_id}.23": 1,
}
RARITAN_EXT_SENS_DECIMAL_DIGITS = {
    "1.3.6.1.4.1.13742.6.3.6.3.1.17.{item_id}.1": 1,
    "1.3.6.1.4.1.13742.6.3.6.3.1.17.{item_id}.2": 0,
    "1.3.6.1.4.1.13742.6.3.6.3.1.17.{item_id}.3": 1,
    "1.3.6.1.4.1.13742.6.3.6.3.1.17.{item_id}.4": 0,
    "1.3.6.1.4.1.13742.6.3.6.3.1.17.{item_id}.5": 0,
    "1.3.6.1.4.1.13742.6.3.6.3.1.17.{item_id}.6": 0,
    "1.3.6.1.4.1.13742.6.3.6.3.1.17.{item_id}.7": 0,
}

SNMP_ITEMS_TYPE = list[tuple[None, Integer, Integer, list[tuple[ObjectName, Integer]]]]


class SnmpServerSimulator:
    """SNMP server simulator."""

    def __init__(self, log: logging.Logger) -> None:
        self.log = log.getChild(type(self).__name__)
        self.mib_tree_holder = MibTreeHolder()
        self.snmp_items: SNMP_ITEMS_TYPE = []
        self.SYS_DESCR = [
            (
                ObjectName(value=self.mib_tree_holder.mib_tree["sysDescr"].oid + ".0"),
                OctetString(value=SIMULATED_SYS_DESCR),
            )
        ]

    def snmp_cmd(
        self,
        snmp_engine: SnmpEngine,
        auth_data: CommunityData,
        transport_target: UdpTransportTarget,
        context_data: ContextData,
        *var_binds: typing.Any,
        **options: typing.Any,
    ) -> typing.Iterator:
        """Handle all SNMP commands."""

        assert snmp_engine is not None
        assert auth_data is not None
        assert transport_target is not None
        assert context_data is not None
        assert len(options) == 2

        # The pysnmp API is a mess so we need to access "private" members to
        # get the info we want. The noinspection comments keep PyCharm happy.
        assert isinstance(var_binds[0], ObjectType)
        # noinspection PyProtectedMember
        assert isinstance(var_binds[0]._ObjectType__args[0], ObjectIdentity)
        # noinspection PyProtectedMember
        object_identity = var_binds[0]._ObjectType__args[0]._ObjectIdentity__args[0]

        if object_identity == self.mib_tree_holder.mib_tree["system"].oid:
            # Handle the getCmd call for the system description.
            return iter([[None, Integer(0), Integer(0), self.SYS_DESCR]])
        else:
            oid_branch = [
                t
                for t in self.mib_tree_holder.mib_tree
                if self.mib_tree_holder.mib_tree[t].oid == object_identity
            ]
            if len(oid_branch) != 1:
                return iter(
                    [[f"Unknown OID {object_identity}.", Integer(0), Integer(0), ""]]
                )

        self.snmp_items = []
        self._generate_snmp_values(object_identity)
        self.log.debug(f"Returning {self.snmp_items=}")
        return iter(self.snmp_items)

    def _generate_snmp_values(self, oid: str) -> None:
        """Helper method to generate SNMP values.

        Parameters
        ----------
        oid : `str`
            The OID to generate a nested list of SNMP values for.
        """
        for elt in self.mib_tree_holder.mib_tree:
            elt_oid = self.mib_tree_holder.mib_tree[elt].oid
            if elt_oid.startswith(oid):
                try:
                    parent = self.mib_tree_holder.mib_tree[elt].parent
                    assert parent is not None
                    if not parent.index:
                        self._append_random_value(elt_oid + ".0", elt)
                    else:
                        self._handle_indexed_item(elt)
                except KeyError:
                    # Deliberately ignored.
                    pass

    def _handle_indexed_item(self, elt: str) -> None:
        """Helper method to handle indexed items.

        Indexed items represent list items and for each index in the list an
        SNMP value needs to be created.

        Parameters
        ----------
        elt : `str`
            The name of the indexed item.
        """
        oid = self.mib_tree_holder.mib_tree[elt].oid

        if oid.startswith(
            self.mib_tree_holder.mib_tree[DeviceName.netbooter.value].oid
        ):
            # Handle PDU indexed items.
            for i in range(PDU_LIST_START_OID, PDU_LIST_START_OID + PDU_LIST_NUM_OIDS):
                self._append_random_value(oid + f".{i}", elt)
        elif oid.startswith(self.mib_tree_holder.mib_tree[DeviceName.xups.value].oid):
            # Handle XUPS indexed items.
            for i in range(
                XUPS_LIST_START_OID, XUPS_LIST_START_OID + XUPS_LIST_NUM_OIDS
            ):
                self._append_random_value(oid + f".{i}", elt)
        elif oid.startswith(
            self.mib_tree_holder.mib_tree[DeviceName.raritan.value].oid
        ):
            self._handle_raritan_indexed_item(elt)
        else:
            self.log.warning(f"Unexpected list item for {oid=!r}.")
            # Handle all other indexed items.
            for i in range(
                MISC_LIST_START_OID, MISC_LIST_START_OID + MISC_LIST_NUM_OIDS
            ):
                self._append_random_value(oid + f".{i}", elt)

    def _append_random_value(self, oid: str, elt: str) -> None:
        """Helper method to generate a random value and append it to the
        existing list of SNMP values.

        Parameters
        ----------
        oid : `str`
            The OID to generate a value for.
        elt : `str`
            The item name which is used for looking up the data type.
        """
        value: Integer | OctetString
        match TelemetryItemType[elt]:
            case "int":
                value = self._generate_integer(oid, 0, 100)
            case "float":
                value = self._generate_float(oid)
            case "string":
                value = self._generate_string(oid)
            case _:
                value = Integer(0)
                self.log.error(
                    f"Unknown telemetry item type {TelemetryItemType[elt]} for {elt=}"
                )
        self._append_value(oid, value)

    def _append_value(self, oid: str, value: Integer | OctetString) -> None:
        """Helper method to append the provided value to the existing list of
        SNMP values.

        Parameters
        ----------
        oid : `str`
            The OID to append the value for.
        value : `Integer` | `OctetString`
            The value to append.
        """
        self.snmp_items.append(
            (None, Integer(0), Integer(0), [(ObjectName(value=oid), value)])
        )

    def _generate_integer(self, oid: str, start: int, stop: int) -> Integer:
        """Generate an Integer value in the specified range.

        Parameters
        ----------
        oid : `str`
            The OID to generate a float value for. Not used except when mocking
            this method.
        start : `int`
            The start of the range to generate an Integer for.
        stop : `int`
            The stop of the range to generate an Integer for.

        Returns
        -------
        Integer
            An SNMP Integer object.
        """
        return Integer(random.randrange(start, stop))

    def _generate_float(self, oid: str) -> Integer | OctetString:
        """Generate a float value.

        Parameters
        ----------
        oid : `str`
            The OID to generate a float value for.

        Returns
        -------
        Integer | OctetString
            An SNMP Integer or OctetString object.
        """
        if oid.startswith(
            self.mib_tree_holder.mib_tree[DeviceName.netbooter.value].oid
        ):
            value = self._generate_netbooter_float(oid)
        elif oid in FREQUENCY_OID_LIST:
            value = Integer(FIFTY_HZ_IN_TENS)
        elif oid in SCHNEIDER_FLOAT_AS_STRING_OID_LIST:
            value = self._generate_schneider_float_string()
        else:
            # SNMP doesn't have floats. Instead an int is used which needs to
            # be cast to a float by the reader.
            value = self._generate_integer(oid, 100, 1000)
        return value

    def _generate_string(self, oid: str) -> OctetString:
        """Generate a string value.

        Parameters
        ----------
        oid : `str`
            The OID to generate a string value for.

        Returns
        -------
        OctetString
            An SNMP OctetString object.
        """
        return OctetString(
            value="".join(random.choices(string.ascii_uppercase + string.digits, k=20))
        )

    def _generate_netbooter_float(self, oid: str) -> Integer | OctetString:
        # Certain Netbooter values are floats encoded as hexadecimal strings of
        # the format "0x<hex value>00".
        if oid in PDU_HEX_OID_LIST:
            float_value = round(random.uniform(0.0, 10.0), 2)
            hex_string = (
                "0x"
                + "".join([format(ord(c), "x") for c in f"{float_value:0.2f}"])
                + "00"
            )
            return OctetString(value=hex_string)
        else:
            return self._generate_integer(oid, 100, 1000)

    def _generate_schneider_float_string(self) -> OctetString:
        # Certain Schneider UPS values are strings that represent float values.
        float_value = random.uniform(0.0, 250.0)
        return OctetString(value=f"{float_value}")

    def _handle_raritan_indexed_item(self, elt: str) -> None:
        """Helper method to handle Raritan indexed items.

        Indexed items represent list items and for each index in the list an
        SNMP value needs to be created.

        Parameters
        ----------
        elt : `str`
            The name of the indexed item.
        """
        oid = RaritanOid(self.mib_tree_holder.mib_tree[elt].oid)
        match oid:
            case RaritanOid.InletDecimalDigits:
                self._generate_raritan_decimal_digits(RARITAN_INLET_DECIMAL_DIGITS, 1)
            case RaritanOid.OutletDecimalDigits:
                self._generate_raritan_decimal_digits(RARITAN_OUTLET_DECIMAL_DIGITS, 48)
            case RaritanOid.ExternalSensorDecimalDigits:
                self._generate_raritan_decimal_digits(
                    RARITAN_EXT_SENS_DECIMAL_DIGITS, 1
                )
            case RaritanOid.InletTelemetry:
                self._generate_raritan_inlet_telemetry()
            case RaritanOid.OutletTelemetry:
                self._generate_raritan_outlet_telemetry()
            case RaritanOid.ExternalSensorTelemetry:
                self._generate_raritan_external_sensor_telemetry()
            case _:
                self.log.warning(f"Unknown Raritan {oid=!r}. Ignoring.")

    def _generate_raritan_decimal_digits(
        self, digits_template: dict[str, int], num_items: int
    ) -> None:
        """Generic method to generate Raritan decimal digits replies.

        For the outlet decimal digits reply, the same values need to be
        repeated 48 times because that's how many outlets each device has. To
        avoid clutter of repeating code, a general method was created with a
        small overhead for the need of defining all decimal digit info as
        templates.

        Parameters
        ----------
        digits_template : `dict[str, int]`
            The decimal digits template to use.
        num_items : `int`
            How often to repeat the info in the template.
        """
        for num_item in range(1, num_items + 1):
            for iid in digits_template:
                self._append_value(
                    f"{iid.format(item_id=num_item)}", Integer(digits_template[iid])
                )

    def _generate_raritan_inlet_telemetry(self) -> None:
        """Helper method to generate Raritan inlet telemetry."""
        prefix = f"{RaritanOid.InletTelemetry.value}.1.1."
        oid = f"{prefix}{RaritanItemId.rmsCurrent.value}"
        self._append_value(oid, self._generate_integer(oid, 3775, 4001))
        oid = f"{prefix}{RaritanItemId.unbalancedCurrent.value}"
        self._append_value(oid, self._generate_integer(oid, 60, 70))
        oid = f"{prefix}{RaritanItemId.rmsVoltage.value}"
        self._append_value(oid, self._generate_integer(oid, 395, 405))
        oid = f"{prefix}{RaritanItemId.activePower.value}"
        self._append_value(oid, self._generate_integer(oid, 1250, 1750))
        oid = f"{prefix}{RaritanItemId.apparentPower.value}"
        self._append_value(oid, self._generate_integer(oid, 1700, 1800))
        oid = f"{prefix}{RaritanItemId.powerFactor.value}"
        self._append_value(oid, self._generate_integer(oid, 0, 100))
        oid = f"{prefix}{RaritanItemId.activeEnergy.value}"
        self._append_value(oid, self._generate_integer(oid, 10000, 15000))
        oid = f"{prefix}{RaritanItemId.frequency.value}"
        self._append_value(oid, self._generate_integer(oid, 495, 505))
        oid = f"{prefix}{RaritanItemId.unbalancedVoltage.value}"
        self._append_value(oid, self._generate_integer(oid, 1, 2))
        oid = f"{prefix}{RaritanItemId.unbalancedLineLineVoltage.value}"
        self._append_value(oid, self._generate_integer(oid, 0, 1))

    def _generate_raritan_outlet_telemetry(self) -> None:
        """Helper method to generate Raritan outlet telemetry."""
        prefix = f"{RaritanOid.OutletTelemetry.value}.1."
        for i in range(1, 49):
            oid = f"{prefix}{i}.{RaritanItemId.rmsCurrent.value}"
            self._append_value(oid, self._generate_integer(oid, 0, 250))
            oid = f"{prefix}{i}.{RaritanItemId.rmsVoltage.value}"
            self._append_value(oid, self._generate_integer(oid, 229, 230))
            oid = f"{prefix}{i}.{RaritanItemId.activePower.value}"
            self._append_value(oid, self._generate_integer(oid, 0, 100))
            oid = f"{prefix}{i}.{RaritanItemId.apparentPower.value}"
            self._append_value(oid, self._generate_integer(oid, 0, 100))
            oid = f"{prefix}{i}.{RaritanItemId.powerFactor.value}"
            self._append_value(oid, self._generate_integer(oid, 0, 100))
            oid = f"{prefix}{i}.{RaritanItemId.activeEnergy.value}"
            self._append_value(oid, self._generate_integer(oid, 10000, 15000))
            oid = f"{prefix}{i}.{RaritanItemId.onOff.value}"
            self._append_value(oid, self._generate_integer(oid, 0, 2))
            oid = f"{prefix}{i}.{RaritanItemId.frequency.value}"
            self._append_value(oid, self._generate_integer(oid, 495, 505))

    def _generate_raritan_external_sensor_telemetry(self) -> None:
        """Helper method to generate Raritan external sensor telemetry."""
        oid = f"{RaritanOid.ExternalSensorTelemetry.value}.1.1"
        self._append_value(oid, self._generate_integer(oid, 100, 250))
        oid = f"{RaritanOid.ExternalSensorTelemetry.value}.1.2"
        self._append_value(oid, self._generate_integer(oid, 10, 70))
        oid = f"{RaritanOid.ExternalSensorTelemetry.value}.1.3"
        self._append_value(oid, self._generate_integer(oid, 100, 250))
        oid = f"{RaritanOid.ExternalSensorTelemetry.value}.1.4"
        self._append_value(oid, self._generate_integer(oid, 10, 70))
        oid = f"{RaritanOid.ExternalSensorTelemetry.value}.1.5"
        self._append_value(oid, self._generate_integer(oid, 0, 1))
        oid = f"{RaritanOid.ExternalSensorTelemetry.value}.1.6"
        self._append_value(oid, self._generate_integer(oid, 0, 1))
        oid = f"{RaritanOid.ExternalSensorTelemetry.value}.1.7"
        self._append_value(oid, self._generate_integer(oid, 0, 1))
