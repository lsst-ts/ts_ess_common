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

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)


class Ld250ProcessorTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_processor(self) -> None:
        device_configuration = common.DeviceConfig(
            name="TestDevice",
            dev_type=common.DeviceType.FTDI,
            dev_id="ABCDEF",
            sens_type=common.SensorType.LD250,
            baud_rate=9600,
            location="Test1",
            safe_interval=2,
        )
        evt_sensor_status = AsyncMock()
        evt_lightning_strike = AsyncMock()
        tel_lightning_strike_status = AsyncMock()
        topics = types.SimpleNamespace(
            **{
                "evt_sensorStatus": evt_sensor_status,
                "evt_lightningStrike": evt_lightning_strike,
                "tel_lightningStrikeStatus": tel_lightning_strike_status,
            }
        )
        log = logging.getLogger()
        processor = common.processor.Ld250Processor(device_configuration, topics, log)

        timestamp = 12345.0
        response_code = 0
        corrected_distance = 125.0
        uncorrected_distance = 125.0
        bearing = 51.0
        sensor_data = [
            common.LD250TelemetryPrefix.STRIKE_PREFIX,
            corrected_distance,
            uncorrected_distance,
            bearing,
        ]
        await processor.process_telemetry(
            timestamp=timestamp,
            response_code=response_code,
            sensor_data=sensor_data,
        )
        evt_lightning_strike.set_write.assert_called_with(
            sensorName=device_configuration.name,
            correctedDistance=corrected_distance,
            uncorrectedDistance=uncorrected_distance,
            bearing=bearing,
        )

        close_strike_rate = 1.0
        total_strike_rate = 1.0
        close_alarm_status = 1
        severe_alarm_status = 1
        heading = 51.0
        sensor_data = [
            common.LD250TelemetryPrefix.STATUS_PREFIX,
            close_strike_rate,
            total_strike_rate,
            close_alarm_status,
            severe_alarm_status,
            heading,
        ]
        await processor.process_telemetry(
            timestamp=timestamp,
            response_code=response_code,
            sensor_data=sensor_data,
        )
        evt_sensor_status.set_write.assert_called_with(
            sensorName=device_configuration.name, sensorStatus=0, serverStatus=0
        )
        tel_lightning_strike_status.set_write.assert_called_with(
            sensorName=device_configuration.name,
            closeStrikeRate=close_strike_rate,
            totalStrikeRate=total_strike_rate,
            closeAlarmStatus=False,
            severeAlarmStatus=False,
            heading=heading,
            timestamp=timestamp,
            location=device_configuration.location,
        )
