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

__all__ = ["GecThermalscannerSensor"]

from ..constants import SensorType, TelemetryDataType
from .base_sensor import BaseSensor
from .sensor_registry import register_sensor


class GecThermalscannerSensor(BaseSensor):
    """GEC Instruments

    Perform protocol conversion for a :ref:`Gec Intrument Scanner.`

    Parameters
    ----------
    log : `logger`
        The logger for which to create a child logger.
    """

    async def extract_telemetry(self, line: str) -> TelemetryDataType:
        """Extract the wind telemetry from a line of Sensor data.

        Parameters
        ----------
        line : `str`
            A line of comma separated telemetry as described in the doc string
            of this class.

        Returns
        -------
        `list`
            A list of 94 floats containing the temperature telemetry as
            measured by the sensor.
        """
        temperatures = line.split(",")
        if len(temperatures) != 94:
            raise ValueError(f"Wrong number of temperature measurements in line {line}")
        return [float(t) for t in line.split(",")]


register_sensor(SensorType.GECTHERMALSCANNER, GecThermalscannerSensor)
