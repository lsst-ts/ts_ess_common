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

__all__ = ["compute_signature", "Csat3bSensor"]

import logging

import numpy as np

from ..constants import SensorType
from .base_sensor import BaseSensor
from .sensor_registry import register_sensor

# The number of values in each telemetry string.
_NUM_VALUES = 7

# The range of an unsigned short which is [0, 255]
_SHORT_RANGE = 0x100

# The range of an unsigned word which is [0, 65535]
_WORD_RANGE = 0x10000

# Default output of NaN values in case of an error reading the sensor. Note
# that the final three values are int values and therefore cannot be NaN.
_NANS_OUTPUT: list[float | int | str] = [np.nan, np.nan, np.nan, np.nan, 0, 0, 0]


def compute_signature(input_str: str, delimiter: str) -> int:
    """Compute the signature of the sensor telemetry.

    The computation is based on the C function that can be found on page
    55 of csat3b.pdf in the doc directory.

    Parameters
    ----------
    input_str : `str`
        The string of telemetry for which to compute the signature.
    delimiter: `str`
        The delimiter used in input_str.

    Returns
    -------
    `int`
        The signature.

    Notes
    -----
    By experiment it was found that the description of the input string on
    page 55 of the document is incorrect. The description states that all
    data from "x" to "c" are used but by implementing the C function in a C
    source file and calling the function it was established that only "x"
    up to "d" are used.
    For compatibility sake, the input string is expected to contain the
    value of "c" plus a leading delimiter and this Python implementation
    strips that value and delimiter before computing the signature.
    """
    # Remove the value of "c" plus the leading delimiter from the input
    # string otherwise an incorrect signature is computed.
    last_index = input_str.rfind(delimiter)
    input_str = input_str[:last_index]

    # This is a Python version of the C function.
    seed = 0xAAAA
    msb = seed >> 8
    # Ensure that the value of lsb is in the range of a C unsigned short.
    lsb = seed % _SHORT_RANGE
    b = 0
    for char in input_str:
        # Ensure that the value of b is in the range of a C unsigned short.
        b = ((lsb << 1) + msb + ord(char)) % _SHORT_RANGE
        if lsb & 0x80:
            b = b + 1
        msb = lsb
        lsb = b
    # Ensure that the return value is in the range of a C unsigned word.
    return ((msb << 8) + lsb) % _WORD_RANGE


class Csat3bSensor(BaseSensor):
    """CSAT3B Sensor.

    Perform protocol conversion for Campbell Scientific CSAT3B Anemometer
    instruments. Serial data is output by the anemometer once per 100 ms with
    the following format:

        'X,Y,Z,T,D,C,S<CR>'

    where:

        X         x-axis wind speed (m/s). Decimal value.
        Y         y-axis wind speed (m/s). Decimal value.
        Z         z-axis wind speed (m/s). Decimal value.
        T         Sonic temperature (degrees C). Decimal value.
        D         Diagnostic word. Single digit decimal.
        C         Record counter. One or two digit value (0-63).
        S         Signature. Four character lower case hexadecimal value
                  without the leading '0x'. See page 55 of csat3b.pdf in the
                  doc directory for examples.
        <CR>      1-character terminator ('\r').

    Parameters
    ----------
    log : `logger`
        The logger for which to create a child logger.
    """

    def __init__(
        self,
        log: logging.Logger,
    ) -> None:
        super().__init__(log=log)

        # Override default value.
        self.terminator = "\r"
        # Override default value.
        self.charset = "ISO-8859-1"

    async def extract_telemetry(self, line: str) -> list[float | int | str]:
        """Extract the telemetry from a line of Sensor data.

        Parameters
        ----------
        line : `str`
            A line of comma separated telemetry as described in the doc string
            of this class.

        Returns
        -------
        `list`
            A list of floats and ints containing the telemetry as measured by
            the sensor. See the description in the doc string of this class.
        """
        stripped_line: str = line.strip(self.terminator)
        line_items = stripped_line.split(self.delimiter)
        output: list[float | int | str] = []
        if len(line_items) == _NUM_VALUES:
            x = float(line_items[0])
            y = float(line_items[1])
            z = float(line_items[2])
            t = float(line_items[3])
            d = int(line_items[4])
            c = int(line_items[5])
            s = int(line_items[6], 16)
            output = [x, y, z, t, d, c, s]
        else:
            output = _NANS_OUTPUT
        return output


register_sensor(SensorType.CSAT3B, Csat3bSensor)
