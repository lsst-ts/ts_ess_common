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

import asyncio
import logging
import unittest

from lsst.ts.ess import common
from lsst.ts.ess.common.test_utils import MockTestTools

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)


class MockDeviceTestCase(unittest.IsolatedAsyncioTestCase):
    async def _callback(self, reply: dict[str, list[str | float]]) -> None:
        self.reply: None | dict[str, list[str | float]] = reply

    async def _check_mock_ld250_device(
        self,
        in_error_state: bool = False,
        noise: bool = False,
        strike: bool = False,
    ) -> None:
        """Check the working of the MockDevice."""
        log = logging.getLogger(type(self).__name__)
        mtt = MockTestTools()
        sensor = common.sensor.Ld250Sensor(log=log)
        sensor_name = "MockSensor"
        async with common.device.MockDevice(
            name=sensor_name,
            device_id="MockDevice",
            sensor=sensor,
            callback_func=self._callback,
            log=log,
        ) as device:
            device.noise = noise
            device.strike = strike

            self.reply = None
            while not self.reply:
                await asyncio.sleep(0.1)
            reply_to_check = self.reply[common.Key.TELEMETRY]
            mtt.check_ld250_reply(
                reply=reply_to_check,
                name=sensor_name,
                in_error_state=in_error_state,
            )

    async def test_mock_ld250_device(self) -> None:
        """Test the MockDevice with a nominal configuration, i.e. no
        disconnected channels and no truncated data.
        """
        await self._check_mock_ld250_device()

    async def test_mock_ld250_device_noise(self) -> None:
        """Test the MockDevice when it produces noise telemetry."""
        await self._check_mock_ld250_device(noise=True)

    async def test_mock_ld250_device_strike(self) -> None:
        """Test the MockDevice when it produces strike telemetry."""
        await self._check_mock_ld250_device(strike=True)
