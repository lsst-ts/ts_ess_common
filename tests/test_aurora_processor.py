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


class AuroraProcessorTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_processor(self) -> None:
        location = "DIMM"
        device_config = common.DeviceConfig(
            name="TestDevice",
            location=location,
            dev_type=common.DeviceType.SERIAL,
            sens_type=common.SensorType.AURORA,
            baud_rate=9600,
        )

        evt_sensor_status = AsyncMock()
        tel_temperature = AsyncMock()
        topics = types.SimpleNamespace(
            **{
                "evt_sensorStatus": evt_sensor_status,
                "tel_temperature": tel_temperature,
            }
        )
        log = logging.getLogger()
        sensor = common.sensor.AuroraSensor(log=log)
        processor = common.processor.AuroraProcessor(
            device_configuration=device_config,
            topics=topics,
            log=log,
        )

        timestamp = 12345.0
        response_code = 0

        sensor_data = common.sensor.AuroraSensorData(
            seq_num=123,
            ambient_temperature=15.2,
            sky_temperature=-9.12,
            clarity=25.02,
            light_level=0,
            rain_level=0,
            alarm=5,
        )
        sensor_line = "$20,ff,00123,01520,-0912,02502,000,000,0000,0000,05,00!\n"
        expected_temperatures = [
            sensor_data.ambient_temperature,
            sensor_data.sky_temperature,
            sensor_data.clarity,
        ]

        sensor_output = await sensor.extract_telemetry(sensor_line)
        await processor.process_telemetry(
            timestamp=timestamp,
            response_code=response_code,
            sensor_data=sensor_output,
        )
        evt_sensor_status.set_write.assert_called_with(
            sensorName=device_config.name, sensorStatus=5, serverStatus=0
        )
        tel_temperature.set_write.assert_called()
        args, kwargs = tel_temperature.set_write.call_args

        self.assertEqual(kwargs["sensorName"], device_config.name)
        self.assertAlmostEqual(kwargs["timestamp"], timestamp, places=3)
        self.assertEqual(kwargs["numChannels"], len(expected_temperatures))
        for expected, actual in zip(expected_temperatures, kwargs["temperatureItem"]):
            self.assertAlmostEqual(expected, actual, places=3)
        self.assertEqual(kwargs["location"], location)

        self.assertEqual(len(args), 0)
        self.assertEqual(len(kwargs), 5)
