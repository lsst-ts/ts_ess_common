# This file is part of ts_ess_common.
#
# Developed for the Vera C. Rubin Observatory Telescope and Site Systems.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
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
import unittest
from unittest.mock import AsyncMock

from lsst.ts.ess import common


class WindsonicProcessorTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_processor(self) -> None:
        device_configuration = common.DeviceConfig(
            name="TestDevice",
            dev_type=common.DeviceType.FTDI,
            dev_id="ABCDEF",
            sens_type=common.SensorType.WINDSONIC,
            baud_rate=9600,
            location="Test1",
            num_samples=4,
        )
        evt_sensor_status = AsyncMock()
        tel_air_flow = AsyncMock()
        topics = types.SimpleNamespace(
            **{
                "evt_sensorStatus": evt_sensor_status,
                "tel_airFlow": tel_air_flow,
            }
        )
        log = logging.getLogger()
        processor = common.processor.WindsonicProcessor(
            device_configuration, topics, log
        )

        timestamp = 12345.0
        response_code = 0
        sensor_data = [1.0, 2.0]
        for _ in range(device_configuration.num_samples):
            await processor.process_telemetry(
                timestamp=timestamp,
                response_code=response_code,
                sensor_data=sensor_data,
            )
        evt_sensor_status.set_write.assert_called_with(
            sensorName=device_configuration.name, sensorStatus=0, serverStatus=0
        )
        tel_air_flow.set_write.assert_called_with(
            sensorName=device_configuration.name,
            timestamp=timestamp,
            location=device_configuration.location,
            direction=2.0,
            directionStdDev=-0.0,
            maxSpeed=1.0,
            speed=1.0,
            speedStdDev=0.0,
        )
