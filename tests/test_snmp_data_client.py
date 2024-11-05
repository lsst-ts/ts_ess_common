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

import logging
import types
import typing
import unittest
from unittest.mock import AsyncMock, MagicMock

from lsst.ts.ess import common
from lsst.ts.xml.component_info import ComponentInfo

ADDITIONAL_TOPICS_NUM_CALLS = {
    "tel_temperature": 1,
    "tel_relativeHumidity": 2,
}


class SnmpDataClientTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_snmp_data_client(self) -> None:
        log = logging.getLogger()
        for device_type in [device_name.value for device_name in common.DeviceName]:
            component_info = ComponentInfo(name="ESS", topic_subname="")
            topic_name = f"tel_{device_type}"
            # TODO DM-46349 Remove this if as soon as the next XML after 22.1
            #  is released.
            if topic_name not in component_info.topics:
                return
            tel_topics: dict[str, AsyncMock] = {}
            topic_names = [topic_name]
            if device_type == common.DeviceName.raritan.value:
                topic_names += ADDITIONAL_TOPICS_NUM_CALLS.keys()
            for tn in topic_names:
                tel_topic = AsyncMock()
                dt = await self.mock_data_type(component_info, tn)
                tel_topic.DataType = MagicMock(return_value=dt)
                tel_topic.topic_info.fields = component_info.topics[tn].fields
                tel_topic.metadata.field_info = component_info.topics[tn].fields
                tel_topics[tn] = tel_topic
            self.topics = types.SimpleNamespace(**tel_topics)
            config = types.SimpleNamespace(
                host="localhost",
                port=161,
                max_read_timeouts=5,
                device_name="TestDevice",
                device_type=device_type,
                snmp_community="public",
                poll_interval=0.1,
            )
            snmp_data_client = common.data_client.SnmpDataClient(
                config=config, topics=self.topics, log=log, simulation_mode=1
            )
            await snmp_data_client.setup_reading()
            assert snmp_data_client.system_description == common.SIMULATED_SYS_DESCR

            await snmp_data_client.read_data()

            await self.assert_set_write(topic_name, 1)

            if device_type == common.DeviceName.raritan.value:
                for topic_name in ADDITIONAL_TOPICS_NUM_CALLS:
                    await self.assert_set_write(
                        topic_name, ADDITIONAL_TOPICS_NUM_CALLS[topic_name]
                    )

    async def mock_data_type(
        self, component_info: ComponentInfo, topic_name: str
    ) -> types.SimpleNamespace:
        """Mock the DataType of a telemetry topic.

        Parameters
        ----------
        component_info : `ComponentInfo`
            The component info derived from the ESS XML files.
        topic_name : `str`
            The telemetry topic name.

        Returns
        -------
        typing.SimpleNamespace
            A SimpleNameSpace representing the DataType.
        """
        telemetry_items: dict[str, typing.Any] = {}
        fields = component_info.topics[topic_name].fields
        for field in fields:
            field_info = component_info.topics[topic_name].fields[field]
            sal_type = field_info.sal_type
            count = field_info.count
            match sal_type:
                case "int":
                    if count == 1:
                        telemetry_items[field] = 0
                    else:
                        telemetry_items[field] = [0 for _ in range(count)]
                case "float" | "double":
                    if count == 1:
                        telemetry_items[field] = 0.0
                    else:
                        telemetry_items[field] = [0.0 for _ in range(count)]
                case "string":
                    if count == 1:
                        telemetry_items[field] = ""
                    else:
                        telemetry_items[field] = ["" for _ in range(count)]
        data_type = types.SimpleNamespace(**telemetry_items)
        return data_type

    async def assert_set_write(self, topic_name: str, call_count: int) -> None:
        """Assert the call to `set_write`.

        `set_write` gets called with kwargs representing the telemetry items
        specific to the telemetry topic, i.e. not the `private` items, which
        are generic to all telemetry topics. Most telemetry topics get called
        once, but some get called more than once.

        This method verifies that all items in the DataType of the telemetry
        topic are present in the call keyword arguments of `set_write`, that
        the length of the argment is equal to that of the DataType variable in
        case of a list variable and that the telemetry topic gets called the
        expected amount of times.
        """
        tel_topic = getattr(self.topics, topic_name)
        set_write = tel_topic.set_write

        # First assert that the set_write method gets called the expected
        # amount of times.
        assert set_write.call_count == call_count

        # Then assert that the size of the call_args_list is the expected
        # amount.
        call_args_list = set_write.call_args_list
        assert len(call_args_list) == call_count

        # Finally assert that the call arguments are of the expected data type
        # and, if a list, of the expected length.
        for call_args in call_args_list:
            data_type = tel_topic.DataType()
            for var in vars(data_type):
                if var in call_args.kwargs:
                    call_arg = call_args.kwargs[var]
                    data_type_item = getattr(data_type, var)
                    assert isinstance(call_arg, type(data_type_item))
                    if isinstance(data_type_item, list):
                        assert len(call_arg) == len(data_type_item)
