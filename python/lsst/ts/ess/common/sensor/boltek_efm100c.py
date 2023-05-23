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

    Perform protocol conversion for the
    :ref:`Boltek EFM-100C Atmospheric Electric Field Monitor
    <lsst.ts.ess.common.boltek_LD-250_sensor>`.
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
