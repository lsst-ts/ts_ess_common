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


class AuxTelCameraCoolantPressureProcessorTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_processor(self) -> None:
        device_configuration = common.DeviceConfig(
            name="TestDevice",
            dev_type=None,
            dev_id="TestId",
            sens_type=None,
            baud_rate=0,
            location="TestLocation",
        )
        evt_sensor_status = AsyncMock()
        tel_pressure = AsyncMock()
        tel_pressure.DataType = MagicMock(
            return_value=types.SimpleNamespace(pressureItem=[0.0, 0.0, 0.0, 0.0])
        )
        topics = types.SimpleNamespace(
            **{
                "evt_sensorStatus": evt_sensor_status,
                "tel_pressure": tel_pressure,
            }
        )
        log = logging.getLogger()
        processor = common.processor.AuxTelCameraCoolantPressureProcessor(
            device_configuration, topics, log
        )

        timestamp = 12345.0
        response_code = 0
        pressure_item = 750000.0
        await processor.process_telemetry(
            timestamp=timestamp,
            response_code=response_code,
            sensor_data=[pressure_item],
        )
        evt_sensor_status.set_write.assert_called_with(
            sensorName=device_configuration.name, sensorStatus=0, serverStatus=0
        )
        tel_pressure.set_write.assert_called_with(
            sensorName=device_configuration.name,
            timestamp=timestamp,
            pressureItem=[pressure_item, np.nan, np.nan, np.nan],
            numChannels=1,
            location=device_configuration.location,
        )
