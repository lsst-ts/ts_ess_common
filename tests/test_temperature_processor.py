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
from unittest.mock import ANY, AsyncMock, MagicMock

import numpy as np
from lsst.ts.ess import common


class TemperatureProcessorTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_processor(self) -> None:
        device_configuration = common.DeviceConfig(
            name="TestDevice",
            dev_type=common.DeviceType.FTDI,
            dev_id="ABCDEF",
            sens_type=common.SensorType.TEMPERATURE,
            baud_rate=9600,
            location="Unused, Test1, Test2, unused, Test3, Test4",
            num_channels=6,
        )
        evt_sensor_status = AsyncMock()
        tel_temperature = AsyncMock()
        tel_temperature.DataType = MagicMock(
            return_value=types.SimpleNamespace(temperatureItem=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        )
        topics = types.SimpleNamespace(
            **{
                "evt_sensorStatus": evt_sensor_status,
                "tel_temperature": tel_temperature,
            }
        )
        log = logging.getLogger()
        processor = common.processor.TemperatureProcessor(device_configuration, topics, log)

        timestamp = 12345.0
        response_code = 0
        sensor_data = [1.0, 2.0, 3.0, 4.0, 5.0, None]
        # Any None value in the sensor data will be replaced with NaN, which is
        # why the last value in the following list must be set to NaN.
        expected_sensor_data = [np.nan, 2.0, 3.0, np.nan, 5.0, np.nan]
        await processor.process_telemetry(
            timestamp=timestamp,
            response_code=response_code,
            sensor_data=sensor_data,
        )
        evt_sensor_status.set_write.assert_called_with(
            sensorName=device_configuration.name, sensorStatus=0, serverStatus=0
        )
        # Asserts don't handle data with NaN values well which is why the
        # expected value for temperatureItem is set to ANY.
        tel_temperature.set_write.assert_called_with(
            sensorName=device_configuration.name,
            timestamp=timestamp,
            temperatureItem=ANY,
            numChannels=device_configuration.num_channels,
            location=device_configuration.location,
        )

        # Work around assert not handling data with NaN values well. Also make
        # sure that there are no None values.
        for mock_call in tel_temperature.mock_calls:
            if "temperatureItem" in mock_call.kwargs:
                temperature_item = mock_call.kwargs["temperatureItem"]
                assert None not in temperature_item
                for index, _ in enumerate(temperature_item):
                    if np.isnan(temperature_item[index]):
                        assert np.isnan(expected_sensor_data[index])
                    else:
                        assert temperature_item[index] == expected_sensor_data[index]
