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
import unittest

import numpy as np
from lsst.ts.ess import common

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)


class Efm100cSensorTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_extract_telemetry(self) -> None:
        self.log = logging.getLogger(type(self).__name__)
        self.sensor = common.sensor.Efm100cSensor(self.log)

        line = "$+10.65,0*CE\r\n"
        reply = await self.sensor.extract_telemetry(line=line)
        assert reply == [10.65, 0.0]

        line = "$+00.64,0*CD\r\n"
        reply = await self.sensor.extract_telemetry(line=line)
        assert reply == [0.64, 0.0]

        line = "$-19.11,0*CD\r\n"
        reply = await self.sensor.extract_telemetry(line=line)
        assert reply == [-19.11, 0.0]

        line = "$+00.00,0*CD\r\n"
        reply = await self.sensor.extract_telemetry(line=line)
        assert reply == [0.0, 0.0]

        line = "$-11.45,1*CD\r\n"
        reply = await self.sensor.extract_telemetry(line=line)
        assert reply == [-11.45, 1.0]

        line = "$11.45,0*CD\r\n"
        reply = await self.sensor.extract_telemetry(line=line)
        assert reply == [np.nan, 1.0]

        line = "$+1.45,0*CD\r\n"
        reply = await self.sensor.extract_telemetry(line=line)
        assert reply == [np.nan, 1.0]

        line = "$+1.45,0*CD"
        reply = await self.sensor.extract_telemetry(line=line)
        assert reply == [np.nan, 1.0]
