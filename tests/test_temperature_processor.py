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
from unittest.mock import AsyncMock, MagicMock

from lsst.ts.ess import common

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)


class TemperatureProcessorTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_processor(self) -> None:
        device_configuration = common.DeviceConfig(
            name="TestDevice",
            dev_type=common.DeviceType.FTDI,
            dev_id="ABCDEF",
            sens_type=common.SensorType.TEMPERATURE,
            baud_rate=9600,
            location="Test1",
            num_channels=4,
        )
        evt_sensor_status = AsyncMock()
        tel_temperature = AsyncMock()
        tel_temperature.DataType = MagicMock(
            return_value=types.SimpleNamespace(temperatureItem=[0.0, 0.0, 0.0, 0.0])
        )
        topics = types.SimpleNamespace(
            **{
                "evt_sensorStatus": evt_sensor_status,
                "tel_temperature": tel_temperature,
            }
        )
        log = logging.getLogger()
        processor = common.processor.TemperatureProcessor(
            device_configuration, topics, log
        )

        timestamp = 12345.0
        response_code = 0
        sensor_data = [1.0, 2.0, 3.0, 4.0]
        await processor.process_telemetry(
            timestamp=timestamp,
            response_code=response_code,
            sensor_data=sensor_data,
        )
        evt_sensor_status.set_write.assert_called_with(
            sensorName=device_configuration.name, sensorStatus=0, serverStatus=0
        )
        tel_temperature.set_write.assert_called_with(
            sensorName=device_configuration.name,
            timestamp=timestamp,
            temperatureItem=sensor_data,
            numChannels=device_configuration.num_channels,
            location=device_configuration.location,
        )
