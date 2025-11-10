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

__all__ = ["TemperatureSensor"]

import numpy as np

from ..constants import DISCONNECTED_VALUE, SensorType, TelemetryDataType
from .base_sensor import BaseSensor
from .sensor_registry import register_sensor
from .utils import add_missing_telemetry


class TemperatureSensor(BaseSensor):
    """SEL multi-channel temperature reader.

    Perform protocol conversion for a :ref:`SEL multi-channel temperature
    reader <lsst.ts.ess.common.sel_multi_channel_temperature_reader>`.

    Parameters
    ----------
    log : `logger`
        The logger for which to create a child logger.
    num_channels : `int`
        The number of temperature channels.
    """

    async def extract_telemetry(self, line: str) -> TelemetryDataType:
        """Extract the temperature telemetry from a line of Sensor data.

        Parameters
        ----------
        line : `str`
            A line of comma separated telemetry, each of the format
            CXX=XXXX.XXX

        Returns
        -------
        output : `list`
            A list of floats containing the temperature telemetry as measured
            by the sensor. The length of the output list is the same as the
            number of channels.
            If a channel is disconnected (its value will be DISCONNECTED_VALUE)
            or if a channel is missing because the connection to the sensor is
            established mid output, then the value gets replaced by np.nan.
        """
        stripped_line: str = line.strip(self.terminator)
        line_items = stripped_line.split(self.delimiter)
        output: TelemetryDataType = []
        for line_item in line_items:
            temperature_items = line_item.split("=")
            if len(temperature_items) == 1:
                output.append(np.nan)
            elif len(temperature_items) == 2:
                if temperature_items[1] == DISCONNECTED_VALUE:
                    output.append(np.nan)
                else:
                    output.append(float(temperature_items[1]))
            else:
                raise ValueError(f"At most one '=' symbol expected in temperature item {line_item}")

        # When the connection is first made, it may be done while the sensor is
        # in the middle of outputting data. In that case, only a partial string
        # with the final channels will be received and the missing leading
        # channels need to be filled with NaN.
        output = add_missing_telemetry(output, self.num_channels)
        return output


register_sensor(SensorType.TEMPERATURE, TemperatureSensor)
