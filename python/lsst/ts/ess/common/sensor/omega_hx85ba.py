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

__all__ = ["Hx85baSensor"]

import numpy as np

from ..constants import SensorType, TelemetryDataType
from .base_sensor import BaseSensor
from .sensor_registry import register_sensor
from .utils import add_missing_telemetry, compute_dew_point_magnus

"""The number of output values for this sensor is 3."""
NUM_VALUES = 3


class Hx85baSensor(BaseSensor):
    """Omega HX85BA Humidity Sensor.

    Perform protocol conversion for a :ref:`Omega HX85BA Humidity Sensor
    <lsst.ts.ess.common.omega_hx80a_series_sensors>`.

    The HX85BA measure barometric pressure, in addition to relative humidity
    and air temperature. It then uses the :ref:`Magnus formula
    <lsst.ts.ess.common.magnus_dewpoint_formula>` to compute dew point.

    Parameters
    ----------
    log : `logger`
        The logger for which to create a child logger.
    """

    # Override default value.
    terminator = "\n\r"
    # Override default value.
    charset = "ISO-8859-1"

    async def extract_telemetry(self, line: str) -> TelemetryDataType:
        """Extract the telemetry from a line of Sensor data.

        Parameters
        ----------
        line : `str`
            A line of comma separated telemetry.

        Returns
        -------
        output : `list`
            A list of 3 floats containing the telemetry as measured by the
            sensor: the relative humidity, the temperature and the barometric
            pressure.
            If a value is missing because the connection to the sensor is
            established mid output, then the value gets replaced by np.nan.
        """
        stripped_line: str = line.strip(self.terminator)
        line_items = stripped_line.split(self.delimiter)
        output: TelemetryDataType = []
        for line_item in line_items:
            telemetry_items = line_item.split("=")
            if len(telemetry_items) == 1:
                output.append(np.nan)
            elif len(telemetry_items) == 2:
                output.append(float(telemetry_items[1]))
            else:
                raise ValueError(
                    f"At most one '=' symbol expected in telemetry item {line_item}"
                )

        # When the connection is first made, it may be done while the sensor is
        # in the middle of outputting data. In that case, only a partial string
        # with the final channels will be received and the missing leading
        # channels need to be filled with NaN.
        output = add_missing_telemetry(output, NUM_VALUES)

        # Add the computed dew point to the output. The casts to float are
        # necessary to keep mypy happy.
        dew_point = compute_dew_point_magnus(
            relative_humidity=float(output[0]), temperature=float(output[1])
        )
        output.append(dew_point)

        return output


register_sensor(SensorType.HX85BA, Hx85baSensor)
