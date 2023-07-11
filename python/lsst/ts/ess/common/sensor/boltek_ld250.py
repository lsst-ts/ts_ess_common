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

__all__ = ["Ld250Sensor"]

import re

from ..constants import LD250TelemetryPrefix, SensorType, TelemetryDataType
from .base_sensor import BaseSensor
from .sensor_registry import register_sensor

"""A regex pattern for a noise telemetry line."""
NOISE_PATTERN = re.compile(
    rf"^\$({LD250TelemetryPrefix.NOISE_PREFIX.value})\*[0-9A-F]{{2}}\r\n$"
)

"""A regex pattern for a status telemetry line."""
STATUS_PATTERN = re.compile(
    rf"^\$({LD250TelemetryPrefix.STATUS_PREFIX.value}),"
    r"(\d{1,3}),(\d{1,3}),(\d{1,2}),(\d{1,2}),(\d\d\d\.\d)\*[0-9A-F]{2}\r\n$"
)

"""A regex pattern for a strike telemetry line."""
STRIKE_PATTERN = re.compile(
    rf"^\$({LD250TelemetryPrefix.STRIKE_PREFIX.value}),"
    r"(\d{1,3}),(\d{1,3}),(\d\d\d\.\d)\*[0-9A-F]{2}\r\n$"
)


class Ld250Sensor(BaseSensor):
    """Boltek LD-250 Lightning Detector.

    Perform protocol conversion for the
    :ref:`Boltek LD-250 Lightning Detector
    <lsst.ts.ess.common.boltek_LD-250_sensor>`.

    Parameters
    ----------
    log : `logger`
        The logger for which to create a child logger.
    """

    async def extract_telemetry(self, line: str) -> TelemetryDataType:
        # stripped_line: str = line.strip(self.terminator)
        # line_items = stripped_line.split(self.delimiter)
        output: TelemetryDataType = []

        # Note that group(0) matches the whole pattern so that needs to be
        # skipped whenever groups in the match are accessed.
        status_match = STATUS_PATTERN.match(line)
        strike_match = STRIKE_PATTERN.match(line)
        noise_match = NOISE_PATTERN.match(line)
        if status_match:
            output.append(status_match.group(1))
            output.append(int(status_match.group(2)))
            output.append(int(status_match.group(3)))
            output.append(int(status_match.group(4)))
            output.append(int(status_match.group(5)))
            output.append(float(status_match.group(6)))
        elif strike_match:
            output.append(strike_match.group(1))
            output.append(int(strike_match.group(2)))
            output.append(int(strike_match.group(3)))
            output.append(float(strike_match.group(4)))
        elif noise_match:
            output.append(noise_match.group(1))
        else:
            # Something is wrong so empty output is returned.
            pass
        return output


register_sensor(SensorType.LD250, Ld250Sensor)
