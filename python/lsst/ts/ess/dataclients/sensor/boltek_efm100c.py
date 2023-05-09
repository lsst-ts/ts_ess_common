# This file is part of ts_ess_dataclients.
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

__all__ = ["Efm100cSensor"]

import re

import numpy as np

from ..constants import SensorType, TelemetryDataType
from .base_sensor import BaseSensor
from .sensor_registry import register_sensor

"""A regex pattern for a telemetry line."""
EFS_PATTERN = re.compile(r"^\$([+-]\d\d\.\d\d),([01])\*[0-9a-fA-F]{2}\r\n$")


class Efm100cSensor(BaseSensor):
    """Boltek EFM-100C Electric Field Strength Sensor.

    Perform protocol conversion for Boltek EFM-100C Electric Field Strength
    instruments. Serial data is output by the instrument 20 times per second
    with the following format:

        '$<p><ee.ee>,<f>*<cs><\r><\n>'

    where:

        $           Start of telemetry indicator.
        p           Polarity of the electric field + or -.
        ee.ee       Electric field level (Range -20.00 kV/m to +20.00 kV/m).
        f           Fault (0: Normal, 1: Rotator fault).
        cs          Hex checksum (Range 00 to FF).
        <\r><\n>    2-character terminator.

    The placeholders shown for the values are displaying the fixed width for
    those values. The values are prepended with zeros and polarity always is
    present, even if the electric field level value is zero or positive (for
    both cases polarity will be +).
    """

    async def extract_telemetry(self, line: str) -> TelemetryDataType:
        efs_match = EFS_PATTERN.match(line)
        if efs_match:
            efs = float(efs_match.group(1))
            fault = int(efs_match.group(2))
        else:
            efs = np.nan
            fault = 1
        output: TelemetryDataType = [efs, fault]
        return output


register_sensor(SensorType.EFM100C, Efm100cSensor)
