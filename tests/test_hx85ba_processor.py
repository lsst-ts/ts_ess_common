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

import numpy as np
from lsst.ts.ess import common

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)


class Hx85baProcessorTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_processor(self) -> None:
        device_configuration = common.DeviceConfig(
            name="TestDevice",
            dev_type=common.DeviceType.FTDI,
            dev_id="ABCDEF",
            sens_type=common.SensorType.HX85BA,
            baud_rate=9600,
            location="Test1",
            num_channels=4,
        )
        evt_sensor_status = AsyncMock()
        tel_dew_point = AsyncMock()
        tel_pressure = AsyncMock()
        tel_pressure.DataType = MagicMock(
            return_value=types.SimpleNamespace(pressureItem=[0.0, 0.0, 0.0, 0.0])
        )
        tel_relative_humidity = AsyncMock()
        tel_temperature = AsyncMock()
        tel_temperature.DataType = MagicMock(
            return_value=types.SimpleNamespace(temperatureItem=[0.0, 0.0, 0.0, 0.0])
        )
        topics = types.SimpleNamespace(
            **{
                "evt_sensorStatus": evt_sensor_status,
                "tel_dewPoint": tel_dew_point,
                "tel_pressure": tel_pressure,
                "tel_relativeHumidity": tel_relative_humidity,
                "tel_temperature": tel_temperature,
            }
        )
        log = logging.getLogger()
        processor = common.processor.Hx85baProcessor(device_configuration, topics, log)

        timestamp = 12345.0
        response_code = 0
        relative_humidity = 1.0
        temperature = 2.0
        pressure = 3.0
        dew_point = 4.0
        sensor_data = [relative_humidity, temperature, pressure, dew_point]
        await processor.process_telemetry(
            timestamp=timestamp,
            response_code=response_code,
            sensor_data=sensor_data,
        )
        evt_sensor_status.set_write.assert_called_with(
            sensorName=device_configuration.name, sensorStatus=0, serverStatus=0
        )
        tel_dew_point.set_write.assert_called_with(
            sensorName=device_configuration.name,
            timestamp=timestamp,
            dewPointItem=dew_point,
            location=device_configuration.location,
        )
        tel_pressure.set_write.assert_called_with(
            sensorName=device_configuration.name,
            timestamp=timestamp,
            pressureItem=[
                common.processor.mbar_to_pa(pressure),
                np.nan,
                np.nan,
                np.nan,
            ],
            numChannels=1,
            location=device_configuration.location,
        )
        tel_relative_humidity.set_write.assert_called_with(
            sensorName=device_configuration.name,
            timestamp=timestamp,
            relativeHumidityItem=relative_humidity,
            location=device_configuration.location,
        )
        tel_temperature.set_write.assert_called_with(
            sensorName=device_configuration.name,
            timestamp=timestamp,
            temperatureItem=[temperature, np.nan, np.nan, np.nan],
            numChannels=1,
            location=device_configuration.location,
        )
