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

import logging
import math
from typing import List

from .base_sensor import BaseSensor
from ..constants import SensorType
from .sensor_registry import register_sensor
from .utils import add_missing_telemetry

"""The number of output values for this sensor is 3."""
NUM_VALUES = 3


class Hx85baSensor(BaseSensor):
    """Omega HX85BA Humidity Sensor.

    Perform protocol conversion for Omega HX85BA Humidity instruments. Serial
    data is output by the instrument once per second with the following
    format:

        '%RH=38.86,AT°C=24.32,Pmb=911.40<\n><\r>'

    where:

        %RH=        Relative Humidity prefix.
        dd.dd       Relative Humidity value (Range 5% to 95%).
        AT°C=       Air Temperature prefix.
        -ddd.dd     Air Temperature value (Range -20C to +120C).
        Pmb=        Barometric Pressure prefix.
        ddd.dd      Barometric Pressure value (10mbar to 1100mbar).
        <LF><CR>    2-character terminator ('\n\r').

    The placeholders shown for the values are displaying the maximum width for
    those values. The values are not prepended with zeros and only show a sign
    in case of a negative value.

    Parameters
    ----------
    log : `logger`
        The logger for which to create a child logger.

    Notes
    -----
    Use the `Magnus formula
    <https://github.com/lsst-ts/ts_ess_common/blob/develop/doc/Dewpoint_Calculation_Humidity_Sensor_E.pdf>`_:: # noqa
        dp = λ·f / (β - f)
        Where:
        • dp is dew point in deg C
        • β = 17.62
        • λ = 243.12 C
        • f = ln(rh/100) + (β·t)/(λ+t))
        • t = air temperature in deg C
        • rh = relative humidity in %
    """

    def __init__(
        self,
        log: logging.Logger,
    ) -> None:
        super().__init__(log=log, num_channels=NUM_VALUES)

        # Override default value.
        self.terminator = "\n\r"
        # Override default value.
        self.charset = "ISO-8859-1"

    @staticmethod
    def compute_dew_point(relative_humidity: float, temperature: float) -> float:
        """Compute dew point using the Magnus formula.

        Parameters
        ----------
        relative_humidity : `float`
            Relative humidity (%)
        temperature : `float`
            Air temperature (C)

        Returns
        -------
        `float`
            Dew point (C)
        """
        β = 17.62
        λ = 243.12
        f = math.log(relative_humidity * 0.01) + β * temperature / (λ + temperature)
        # Return the value truncated at two decimals.
        return λ * f / (β - f)

    async def extract_telemetry(self, line: str) -> List[float]:
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
            established mid output, then the value gets replaced by math.nan.
        """
        self.log.debug("extract_telemetry")
        stripped_line: str = line.strip(self.terminator)
        line_items = stripped_line.split(self.delimiter)
        output = []
        for line_item in line_items:
            telemetry_items = line_item.split("=")
            if len(telemetry_items) == 1:
                output.append(math.nan)
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

        # Add the computed dew point to the output
        dew_point = self.compute_dew_point(
            relative_humidity=output[0], temperature=output[1]
        )
        output.append(dew_point)

        return output


register_sensor(SensorType.HX85BA, Hx85baSensor)
