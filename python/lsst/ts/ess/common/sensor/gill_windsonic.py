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

__all__ = ["WindsonicSensor", "compute_checksum"]

import re

import numpy as np

from ..constants import SensorType, TelemetryDataType
from .base_sensor import BaseSensor
from .sensor_registry import register_sensor


def compute_checksum(checksum_string: str) -> int:
    """Compute the checksum for a Gill Windsonic 2D Sensor.

    Parameters
    ----------
    checksum_string : `str`
        The string for which the checksum is computed.

    Returns
    -------
    checksum : `int`
        The checksum.
    """
    checksum: int = 0
    for i in checksum_string:
        checksum ^= ord(i)
    return checksum


class WindsonicSensor(BaseSensor):
    """GILL Windsonic 2-D Sonic Anemometer Sensor.

    Perform protocol conversion for a :ref:`Gill Windsonic 2-D Sonic
    Anemometer <lsst.ts.ess.common.gill_windsonic_2-d_sonic_wind_sensor>`.

    Parameters
    ----------
    log : `logger`
        The logger for which to create a child logger.
    """

    # ASCII start character.
    start_character: str = "\x02"

    # Unit Identifier.
    unit_identifier: str = "Q"

    # Windspeed unit.
    windspeed_unit: str = "M"

    # Default status.
    good_status: str = "00"

    # ASCII end charactor.
    end_character = "\x03"

    # Default value for the wind direction.
    default_direction_str: str = "999"

    # Default value for the wind speed.
    default_speed_str: str = "9999.9990"

    # Regex pattern to process a line of telemetry.
    telemetry_pattern = re.compile(
        rf"^{start_character}{unit_identifier}{BaseSensor.delimiter}"
        rf"(?P<direction>\d{{3}})?{BaseSensor.delimiter}"
        rf"(?P<speed>\d{{3}}\.\d{{2}}){BaseSensor.delimiter}{windspeed_unit}{BaseSensor.delimiter}"
        rf"(?P<status>\d{{2}}){BaseSensor.delimiter}"
        rf"{end_character}(?P<checksum>[\da-fA-F]{{2}}){BaseSensor.terminator}$"
    )

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
            A list of 2 floats containing the telemetry as measured by the
            sensor: the wind speed and direction.
        """
        m = re.search(self.telemetry_pattern, line)
        if m:
            direction_str = m.group("direction") if m.group("direction") else ""
            speed_str = m.group("speed")
            status = m.group("status")
            checksum_val = int(m.group("checksum"), 16)

            if status != self.good_status:
                self.log.error(f"Expected status {self.good_status} but received {status}. Continuing.")

            checksum_string = (
                f"{self.unit_identifier},{direction_str},{speed_str},{self.windspeed_unit},{status},"
            )
            checksum = compute_checksum(checksum_string)

            if checksum != checksum_val:
                self.log.error(
                    f"Computed checksum {checksum} is not equal to telemetry checksum {checksum_val}."
                )
                speed = np.nan
                direction = np.nan
            else:
                if speed_str == self.default_speed_str:
                    speed = np.nan
                else:
                    speed = float(speed_str)
                if direction_str == self.default_direction_str or direction_str == "":
                    direction = np.nan
                else:
                    direction = int(direction_str)
        elif line == f"{self.terminator}":
            speed = np.nan
            direction = np.nan
        else:
            raise ValueError(f"Received an unparsable line {line}")
        return [speed, direction]


register_sensor(SensorType.WINDSONIC, WindsonicSensor)
