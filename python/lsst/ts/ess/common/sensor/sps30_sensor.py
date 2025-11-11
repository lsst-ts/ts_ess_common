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

__all__ = ["Sps30Sensor", "compute_particulate_checksum"]

import re
from typing import Any

import numpy as np

from ..constants import SensorType, TelemetryDataType
from .base_sensor import BaseSensor
from .sensor_registry import register_sensor


def compute_particulate_checksum(checksum_string: str) -> int:
    """Compute the checksum for Sensirion SPS30 particulate matter sensor data.

    Parameters
    ----------
    checksum_string : `str`
        The string for which the checksum is computed.

    Returns
    -------
    checksum : `int`
        The checksum (sum of all bytes modulo 256).
    """
    checksum: int = 0
    for char in checksum_string:
        checksum += ord(char)
    return checksum % 256


class Sps30Sensor(BaseSensor):
    """Sensirion SPS30 Particulate Matter Sensor.

    Perform protocol conversion for a Sensirion SPS30 particulate matter sensor
    which measures:
    - Particle size concentrations (PM1.0, PM2.5, PM4.0, PM10)
    - Particle number concentrations
    - Typical particle size
    """

    # SPS30 message format constants
    START_CHAR: str = "\x02"
    END_CHAR: str = "\x03"
    GOOD_STATUS: str = "00"

    # Default values for invalid measurements
    DEFAULT_PARTICLE_SIZE: str = "-1.00"
    DEFAULT_CONCENTRATION: str = "-1.000"
    DEFAULT_TYPICAL_SIZE: str = "-1.00"

    # Regex pattern to process SPS30 telemetry
    TELEMETRY_PATTERN = re.compile(
        rf"^{START_CHAR}"
        rf"(?P<sensor_name>[^,]+),"
        rf"(?P<timestamp>\d+\.\d+),"
        rf"(?P<size1>\d+\.\d+),(?P<size2>\d+\.\d+),(?P<size3>\d+\.\d+),"
        rf"(?P<size4>\d+\.\d+),(?P<size5>\d+\.\d+),"
        rf"(?P<conc1>\d+\.\d+),(?P<conc2>\d+\.\d+),(?P<conc3>\d+\.\d+),"
        rf"(?P<conc4>\d+\.\d+),(?P<conc5>\d+\.\d+),"
        rf"(?P<num1>\d+\.\d+),(?P<num2>\d+\.\d+),(?P<num3>\d+\.\d+),"
        rf"(?P<num4>\d+\.\d+),(?P<num5>\d+\.\d+),"
        rf"(?P<typical_size>\d+\.\d+),"
        rf"(?P<location>[^,]+),"
        rf"(?P<status>\d{{2}}){END_CHAR}"
        rf"(?P<checksum>[\da-fA-F]{{2}})\r\n$"
    )

    def __init__(self, log: Any) -> None:
        super().__init__(log=log, num_channels=19)
        self.log = log.getChild(type(self).__name__)
        self.delimiter = ","
        self.terminator = "\n"

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
            return [np.nan] * 17 + ["", ""]

        m = re.search(self.TELEMETRY_PATTERN, line)
        if not m:
            raise ValueError(f"Received unparsable line: {line}")

        try:
            # Verify checksum
            checksum_str = line.split(self.END_CHAR)[0][1:] + m.group("status")
            computed_checksum = compute_particulate_checksum(checksum_str)
            received_checksum = int(m.group("checksum"), 16)

            if computed_checksum != received_checksum:
                raise ValueError(
                    f"Checksum mismatch: computed {computed_checksum}, received {received_checksum}"
                )

            # Verify status
            if m.group("status") != self.GOOD_STATUS:
                self.log.warning(f"Non-zero status received: {m.group('status')}")

            output.append(str(m.group("sensor_name")))
            output.append(float(m.group("timestamp")))

            # Particle sizes
            for i in range(1, 6):
                size = m.group(f"size{i}")
                output.append(np.nan if size == self.DEFAULT_PARTICLE_SIZE else float(size))

            # Matter concentrations
            for i in range(1, 6):
                conc = m.group(f"conc{i}")
                output.append(np.nan if conc == self.DEFAULT_CONCENTRATION else float(conc))

            # Number concentrations
            for i in range(1, 6):
                num = m.group(f"num{i}")
                output.append(np.nan if num == self.DEFAULT_CONCENTRATION else float(num))

            # Typical particle size
            typical_size = m.group("typical_size")
            output.append(np.nan if typical_size == self.DEFAULT_TYPICAL_SIZE else float(typical_size))

            output.append(str(m.group("location")))

        except (ValueError, IndexError) as e:
            self.log.error(f"Error parsing SPS30 data: {e}")
            raise ValueError(f"Failed to parse particulate matter data: {e}")

        return output


register_sensor(SensorType.SPS30, Sps30Sensor)
