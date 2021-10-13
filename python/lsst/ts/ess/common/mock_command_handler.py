# This file is part of ts_ess_common.
#
# Developed for the Vera Rubin Observatory Telescope and Site Systems.
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

__all__ = ["MockCommandHandler"]

import asyncio
import random
import typing

from . import Key, MockTemperatureConfig, ResponseCode
from .abstract_command_handler import AbstractCommandHandler
from lsst.ts import utils


class MockCommandHandler(AbstractCommandHandler):
    """Handle incoming commands and send replies. Apply configuration and read
    sensor data.

    Parameters
    ----------
    callback: `Callable`
        The callback coroutine handling the sensor telemetry. This can be a
        coroutine that sends the data via a socket connection or a coroutine in
        a test class to verify that the command has been handled correctly.
    simulation_mode: `int`
        Indicating if a simulation mode (> 0) or not (0) is active.
    name: `str`
        The name used for the mock telemetry.

    The commands that can be handled are:

        configure: Load the configuration that is passed on with the command
        and connect to the devices specified in that configuration. This
        command can be sent multiple times before a start is received and only
        the last configuration is kept.
        start: Start reading the sensor data of the connected devices and send
        it as plain text via the socket. If no configuration was sent then the
        start command is ignored. Once started no configuration changes can be
        done anymore.
        stop: Stop sending sensor data and disconnect from all devices. Once
        stopped, configuration changes can be done again and/or reading of
        sensor data can be started again.

    """

    def __init__(
        self, callback: typing.Callable, simulation_mode: int, name: str
    ) -> None:
        super().__init__(callback=callback, simulation_mode=simulation_mode)
        self.name = name
        self._telemetry_loop: typing.Optional[asyncio.Future] = None

    async def connect_devices(self) -> None:
        """Mock starting devices."""
        self._telemetry_loop = asyncio.create_task(self._run())

    async def disconnect_devices(self) -> None:
        """Mock stopping devices."""
        assert self._telemetry_loop is not None
        self._telemetry_loop.cancel()
        self._telemetry_loop = None

    async def _run(self) -> None:
        assert self._telemetry_loop is not None
        while not self._telemetry_loop.done():
            # Mock the time needed to output telemetry.
            await asyncio.sleep(1)

            curr_tai: float = utils.current_tai()
            response: int = ResponseCode.OK
            channel_values = [
                float(
                    f"{random.uniform(MockTemperatureConfig.min, MockTemperatureConfig.max):09.4f}"
                )
                for i in range(0, 4)
            ]
            output: typing.List[typing.Union[str, float, int]] = [
                self.name,
                curr_tai,
                response,
                *channel_values,
            ]
            reply = {
                Key.TELEMETRY: output,
            }
            self.log.info(f"Returning {reply}")
            await self._callback(reply)
