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

__all__ = ["AuroraSensor", "AuroraSensorData"]

import logging
from dataclasses import astuple, dataclass

from ..constants import SensorType, TelemetryDataType
from .base_sensor import BaseSensor
from .sensor_registry import register_sensor


@dataclass
class AuroraSensorData:
    """Dataclass representing Aurora Cloud Sensor data.

    Attributes
    ----------
    seq_num : int
        Sequence number (00000 to 99999).
    ambient_temperature : float
        Sensor temperature (°C).
    sky_temperature : float
        Sky temperature (°C).
    clarity : float
        Clarity reading (units unknown).
    light_level : float
        Light intensity (units unknown).
    rain_level : float
        Rain intensity (units unknown).
    alarm : int
        Alarm status code.
    """

    seq_num: int
    ambient_temperature: float
    sky_temperature: float
    clarity: float
    light_level: float
    rain_level: float
    alarm: int

    @staticmethod
    def from_string(data: str) -> "AuroraSensorData":
        """Parse a formatted Aurora Cloud Sensor string into a dataclass."""
        parts = data.strip().split(",")
        return AuroraSensorData(
            seq_num=int(parts[2]),
            ambient_temperature=0.01 * int(parts[3]),
            sky_temperature=0.01 * int(parts[4]),
            clarity=0.01 * int(parts[5]),
            light_level=0.1 * int(parts[6]),
            rain_level=0.1 * int(parts[7]),
            alarm=int(parts[10].split("!")[0]),
        )


class AuroraSensor(BaseSensor):
    """Aurora Cloud Sensor Reader.

    Perform protocol conversion for an `Aurora Cloud Sensor
    <http://www.auroraeurotech.com/CloudSensor.php>`_.

    Parameters
    ----------
    log : `logger`
        The logger for which to create a child logger.
    """

    def __init__(self, log: logging.Logger, num_channels: int):
        self.terminator = "\n"
        assert num_channels == 7
        super().__init__(log=log, num_channels=7)

    async def extract_telemetry(self, line: str) -> TelemetryDataType:
        """Extract the temperature telemetry from a line of Sensor data.

        Parameters
        ----------
        line : `str`
            A line of comma separated telemetry, each of the format
            described in lsst.ts.ess.common.aurora_cloud_sensor_

        Returns
        -------
        output : `list`
            A list of values containing the telemetry as measured
            by the sensor. There are seven elements in the list:
             * Sequence number
             * Sensor (ambient) temperature
             * Sky temperature
             * Clarity, a.k.a. difference between ambient and sky temperature
             * Light level
             * Rain level
             * Alarm code
        """
        reading = AuroraSensorData.from_string(line)
        output = list(astuple(reading))
        return output


register_sensor(SensorType.AURORA, AuroraSensor)
