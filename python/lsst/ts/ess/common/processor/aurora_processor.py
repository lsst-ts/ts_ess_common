# This file is part of ts_ess_common.
#
# Developed for the Vera Rubin Observatory Telescope and Site Systems.
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

from __future__ import annotations

__all__ = ["AuroraProcessor"]

import logging
import types
from collections.abc import Sequence
from typing import TYPE_CHECKING

from ..device_config import DeviceConfig
from ..sensor.aurora_sensor import AuroraSensorData
from .base_processor import BaseProcessor

if TYPE_CHECKING:
    from lsst.ts import salobj


class AuroraProcessor(BaseProcessor):
    def __init__(
        self,
        device_configuration: DeviceConfig,
        topics: salobj.Controller | types.SimpleNamespace,
        log: logging.Logger,
    ) -> None:
        super().__init__(device_configuration, topics, log)

    async def process_telemetry(
        self,
        timestamp: float,
        response_code: int,
        sensor_data: Sequence[float | int | str],
    ) -> None:
        """Process Aurora Cloud Sensor telemetry.

        Parameters
        ----------
        timestamp : `float`
            The timestamp of the data.
        response_code : `int`
            The ResponseCode
        sensor_data : `TelemetryDataType`
            A Sequence representing the sensor telemetry data:
             * Sequence number
             * Sensor (ambient) temperature
             * Sky temperature
             * Clarity, a.k.a. difference between ambient and sky temperature
             * Light level
             * Rain level
             * Alarm code
        """
        reading = AuroraSensorData(
            seq_num=int(sensor_data[0]),
            ambient_temperature=float(sensor_data[1]),
            sky_temperature=float(sensor_data[2]),
            clarity=float(sensor_data[3]),
            light_level=float(sensor_data[4]),
            rain_level=float(sensor_data[5]),
            alarm=int(sensor_data[6]),
        )
        temperature = [
            reading.ambient_temperature,
            reading.sky_temperature,
            reading.clarity,
        ]

        await self.topics.evt_sensorStatus.set_write(
            sensorName=self.device_configuration.name,
            sensorStatus=reading.alarm,
            serverStatus=response_code,
        )

        await self.topics.tel_temperature.set_write(
            sensorName=self.device_configuration.name,
            timestamp=timestamp,
            numChannels=len(temperature),
            temperatureItem=temperature,
            location=self.device_configuration.location,
        )
