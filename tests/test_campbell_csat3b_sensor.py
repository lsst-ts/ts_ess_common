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

import logging
import math
import unittest

import pytest
from lsst.ts.ess import common

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)

# Data from page 55 of csat3b.pdf
DATA = [
    "0.08945,0.06552,0.05726,19.69336,0,5,c3a6",
    "0.10103,0.06517,0.05312,19.70499,0,6,3927",
    "0.09045,0.04732,0.04198,19.71161,0,7,d7e5",
    "0.08199,0.03341,0.03421,19.73416,0,8,4ad9",
    "0.08867,0.03522,0.03378,19.75360,0,9,e314",
    "0.08675,0.02142,0.03289,19.76858,0,10,9b60",
    "0.09035,0.01987,0.03667,19.78433,0,11,931a",
    "0.09960,0.02615,0.04330,19.79236,0,12,14a1",
    "0.09489,0.02513,0.05120,19.79083,0,13,0c0d",
    "0.09513,0.02403,0.05648,19.79037,0,14,c30d",
    "0.10715,0.02723,0.05739,19.78729,0,15,a14c",
    "0.11630,0.03674,0.05579,19.78812,0,16,5cD7",
]


class Csat3bSensorTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_compute_sginature(self) -> None:
        log = logging.getLogger(type(self).__name__)
        sensor = common.sensor.Csat3bSensor(log)
        for line in DATA:
            last_index = line.rfind(",")
            input_line = line[:last_index]
            expected_signature = int(line[last_index + 1 :], 16)
            signature = common.sensor.compute_signature(input_line, sensor.delimiter)
            assert signature == expected_signature

    async def test_extract_telemetry(self) -> None:
        self.log = logging.getLogger(type(self).__name__)
        self.sensor = common.sensor.Csat3bSensor(self.log)

        line = "0.08945,0.06552,0.05726,19.69336,0,5,c3a6\r"
        reply = await self.sensor.extract_telemetry(line=line)
        assert 0.08945 == pytest.approx(reply[0])
        assert 0.06552 == pytest.approx(reply[1])
        assert 0.05726 == pytest.approx(reply[2])
        assert 19.69336 == pytest.approx(reply[3])
        assert 0 == reply[4]
        assert 5 == reply[5]
        assert 0xC3A6 == reply[6]

        # Test with a truncated line, which can be the case with the first
        # telemetry received after connecting to the sensor.
        line = "0.06552,0.05726,19.69336,0,5,c3a6\r"
        reply = await self.sensor.extract_telemetry(line=line)
        assert math.isnan(reply[0])
        assert math.isnan(reply[1])
        assert math.isnan(reply[2])
        assert math.isnan(reply[3])
        assert math.isnan(reply[4])
        assert math.isnan(reply[5])
        assert math.isnan(reply[6])

        # Test with a wrong signature, which can happen in case of a sensor
        # fault or a bit flip.
        line = "0.08945,0.06552,0.05726,19.69336,0,5,c3a7\r"
        reply = await self.sensor.extract_telemetry(line=line)
        assert math.isnan(reply[0])
        assert math.isnan(reply[1])
        assert math.isnan(reply[2])
        assert math.isnan(reply[3])
        assert math.isnan(reply[4])
        assert math.isnan(reply[5])
        assert math.isnan(reply[6])
