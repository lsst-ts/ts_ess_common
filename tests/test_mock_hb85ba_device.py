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
import typing
import unittest

from lsst.ts.ess import common

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)


class MockDeviceTestCase(unittest.IsolatedAsyncioTestCase):
    async def _callback(
        self, reply: typing.Dict[str, typing.List[typing.Union[str, float]]]
    ) -> None:
        self.reply: typing.Optional[
            typing.Dict[str, typing.List[typing.Union[str, float]]]
        ] = reply

    async def _check_mock_hx85ba_device(
        self,
        name: str,
        missed_channels: int = 0,
        in_error_state: bool = False,
    ) -> None:
        """Check the working of the MockDevice."""
        log = logging.getLogger(type(self).__name__)
        mtt = common.MockTestTools()
        sensor = common.sensor.Hx85baSensor(log=log)
        async with common.device.MockDevice(
            name=name,
            device_id="MockDevice",
            sensor=sensor,
            callback_func=self._callback,
            log=log,
        ) as device:
            device.missed_channels = missed_channels
            device.in_error_state = in_error_state

            # First read of the telemetry to verify that handling of truncated
            # data is performed correctly if the MockDevice is instructed to
            # produce such data.
            self.reply = None
            while not self.reply:
                await asyncio.sleep(0.1)
            reply_to_check = self.reply[common.Key.TELEMETRY]
            mtt.check_hx85ba_reply(
                reply=reply_to_check,
                name=name,
                missed_channels=missed_channels,
                in_error_state=in_error_state,
            )

            # Reset missed_channels for the second read otherwise the
            # check will fail.
            if missed_channels > 0:
                missed_channels = 0

            # First read of the telemetry to verify that no more truncated data
            # is produced is the MockDevice was instructed to produce such
            # data.
            self.reply = None
            while not self.reply:
                await asyncio.sleep(0.1)
            reply_to_check = self.reply[common.Key.TELEMETRY]
            mtt.check_hx85ba_reply(
                reply=reply_to_check,
                name=name,
                missed_channels=missed_channels,
                in_error_state=in_error_state,
            )

    async def test_mock_hx85ba_device(self) -> None:
        """Test the MockDevice with a nominal configuration, i.e. no
        disconnected channels and no truncated data.
        """
        await self._check_mock_hx85ba_device(name="MockSensor")

    async def test_mock_hx85ba_device_with_truncated_output(self) -> None:
        """Test the MockDevice with no disconnected channels and truncated data
        for two channels.
        """
        await self._check_mock_hx85ba_device(name="MockSensor", missed_channels=2)

    async def test_mock_hx85ba_device_in_error_state(self) -> None:
        """Test the MockDevice in error state meaning it will only return empty
        strings.
        """
        await self._check_mock_hx85ba_device(name="MockSensor", in_error_state=True)
