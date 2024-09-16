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
from unittest.mock import AsyncMock

from lsst.ts.ess import common
from lsst.ts.xml.component_info import ComponentInfo


class SnmpDataClientTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_snmp_data_client(self) -> None:
        log = logging.getLogger()
        for device_type in ["pdu", "schneiderPm5xxx", "xups"]:
            # TODO DM-46349 Remove this as soon as the next XML after 22.1 is
            #  released.
            component_info = ComponentInfo(name="ESS", topic_subname="")
            if f"tel_{device_type}" not in component_info.topics:
                # No suitable XML version.
                return
            tel_topic = AsyncMock()
            tel_topic.DataType = await self.mock_data_type(component_info, device_type)
            tel_topic.topic_info.fields = component_info.topics[
                f"tel_{device_type}"
            ].fields
            tel_topic.metadata.field_info = component_info.topics[
                f"tel_{device_type}"
            ].fields
            topics = types.SimpleNamespace(**{f"tel_{device_type}": tel_topic})
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
                config=config, topics=topics, log=log, simulation_mode=1
            )
            await snmp_data_client.setup_reading()
            assert snmp_data_client.system_description == common.SIMULATED_SYS_DESCR

            await snmp_data_client.read_data()
            tel_topic = getattr(topics, f"tel_{config.device_type}")
            tel_topic.set_write.assert_called_once()

    async def mock_data_type(
        self, component_info: ComponentInfo, device_type: str
    ) -> types.SimpleNamespace:
        """Mock the DataType of a telemetry topic.

        Parameters
        ----------
        component_info : `ComponentInfo`
            The component info derived from the ESS XML files.
        device_type : `str`
            The type of SNMP device.

        Returns
        -------
        typing.SimpleNamespace
            A SimpleNameSpace representing the DataType.
        """
        telemetry_items: dict[str, typing.Any] = {}
        for field in component_info.topics[f"tel_{device_type}"].fields:
            field_info = component_info.topics[f"tel_{device_type}"].fields[field]
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
