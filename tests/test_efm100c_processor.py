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

import numpy as np
from lsst.ts.ess import common

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)


class Efm100cProcessorTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_processor(self) -> None:
        device_configuration = common.DeviceConfig(
            name="TestDevice",
            dev_type=common.DeviceType.FTDI,
            dev_id="ABCDEF",
            sens_type=common.SensorType.EFM100C,
            baud_rate=9600,
            location="Test1",
            num_samples=4,
            safe_interval=10,
            threshold=10.0,
        )
        evt_sensor_status = AsyncMock()
        evt_high_electric_field = AsyncMock()
        tel_electric_field_strength = AsyncMock()
        topics = types.SimpleNamespace(
            **{
                "evt_sensorStatus": evt_sensor_status,
                "evt_highElectricField": evt_high_electric_field,
                "tel_electricFieldStrength": tel_electric_field_strength,
            }
        )
        log = logging.getLogger()
        processor = common.processor.Efm100cProcessor(device_configuration, topics, log)

        timestamp = 12345.0
        response_code = 0
        sensor_data = [1.0, 0]
        for _ in range(device_configuration.num_samples):
            await processor.process_telemetry(
                timestamp=timestamp,
                response_code=response_code,
                sensor_data=sensor_data,
            )
        evt_sensor_status.set_write.assert_called_with(
            sensorName=device_configuration.name, sensorStatus=0, serverStatus=0
        )
        evt_high_electric_field.set_write.assert_called_with(
            sensorName=device_configuration.name,
            strength=np.nan,
        )
        tel_electric_field_strength.set_write.assert_called_with(
            sensorName=device_configuration.name,
            strength=1.0,
            strengthMax=1.0,
            strengthStdDev=0.0,
            timestamp=12345.0,
            location=device_configuration.location,
        )
