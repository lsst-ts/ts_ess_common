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

from collections.abc import Sequence

from ..sensor.aurora_sensor import AuroraSensorData
from .base_processor import BaseProcessor


class AuroraProcessor(BaseProcessor):
    async def process_telemetry(
        self,
        timestamp: float,
        response_code: int,
        sensor_data: Sequence[float | int | str],
    ) -> None:
        """Process Aurora Cloud Sensor telemetry.

        TODO: DM-49934 The light level and rain level parameters are not
        published to the EFD. An XML revision is needed to accomodate them.

        Parameters
        ----------
        timestamp : `float`
            The timestamp of the data.
        response_code : `int`
            The ResponseCode
        sensor_data : `TelemetryDataType`
            A Sequence representing the sensor telemetry data:
             * Sequence number
             * Sensor (ambient) temperature (°C)
             * Sky temperature (°C)
             * Clarity, a.k.a. difference between ambient and sky temperature
             * Light level (units unknown)
             * Rain level (units unknown)
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
