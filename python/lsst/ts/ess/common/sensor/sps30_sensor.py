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

__all__ = ["Sps30Sensor"]

import re

import numpy as np

from ..constants import PARTICLE_SIZES, SensorType, TelemetryDataType
from .base_sensor import BaseSensor
from .sensor_registry import register_sensor


class Sps30Sensor(BaseSensor):
    """Sensirion SPS30 Particulate Matter Sensor.

    Perform protocol conversion for a Sensirion SPS30 particulate matter sensor
    which measures:
    - Particle size concentrations (PM1.0, PM2.5, PM4.0, PM10)
    - Particle number concentrations
    - Typical particle size
    """

    # Regex pattern to process SPS30 telemetry
    TELEMETRY_PATTERN = re.compile(
        r"(?P<timestamp>\d+\.\d+),"
        r"(?P<conc1>\d+\.\d+),(?P<conc2>\d+\.\d+),(?P<conc3>\d+\.\d+),"
        r"(?P<conc4>\d+\.\d+),(?P<conc5>\d+\.\d+),"
        r"(?P<num1>\d+\.\d+),(?P<num2>\d+\.\d+),(?P<num3>\d+\.\d+),"
        r"(?P<num4>\d+\.\d+),(?P<num5>\d+\.\d+),"
        r"(?P<typical_size>\d+\.\d+)"
    )

    async def extract_telemetry(self, line: str) -> TelemetryDataType:
        """Extract particle measurement telemetry from sensor data.

        Parameters
        ----------
        line : `str`
            A line of SPS30 telemetry data.

        Returns
        -------
        `list`
            A list containing all telemetry fields in the order specified by
            the XML definition. Invalid values are replaced with np.nan for
            numeric fields and empty strings for text fields.

        Raises
        ------
        ValueError
            If the line cannot be parsed or checksum validation fails.
        """
        output: TelemetryDataType = []

        if line.strip() == "":
            self.log.warning("Received empty line from sensor")
            return [""] + [np.nan] * 17 + [""]

        m = re.search(self.TELEMETRY_PATTERN, line)
        if not m:
            self.log.warning(f"Received unparsable line: {line}")
            return [""] + [np.nan] * 17 + [""]

        try:
            output.append(float(m.group("timestamp")))

            # Particle sizes
            output += PARTICLE_SIZES

            # Matter concentrations
            for i in range(1, 6):
                output.append(float(m.group(f"conc{i}")))

            # Number concentrations
            for i in range(1, 6):
                output.append(float(m.group(f"num{i}")))

            # Typical particle size
            output.append(float(m.group("typical_size")))

        except (ValueError, IndexError) as e:
            self.log.error(f"Error parsing SPS30 data: {e}")
            raise ValueError(f"Failed to parse particulate matter data: {e}")

        return output


register_sensor(SensorType.SPS30, Sps30Sensor)
