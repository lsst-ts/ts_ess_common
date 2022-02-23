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

__all__ = ["MockDevice"]

import asyncio
import logging
import time
import typing

from .base_device import BaseDevice
from .mock_formatter import MockFormatter
from .mock_hx85_formatter import MockHx85aFormatter, MockHx85baFormatter
from .mock_temperature_formatter import MockTemperatureFormatter
from ..sensor import BaseSensor, Hx85aSensor, Hx85baSensor, TemperatureSensor


class MockDevice(BaseDevice):
    """Mock Sensor Device.

    Parameters
    ----------
    name : `str`
        The name of the device.
    device_id : `str`
        The hardware device ID to connect to.
    sensor : `BaseSensor`
        The sensor that produces the telemetry.
    callback_func : `Callable`
        Callback function to receive the telemetry.
    log : `logging.Logger`
        The logger to create a child logger for.
    """

    def __init__(
        self,
        name: str,
        device_id: str,
        sensor: BaseSensor,
        callback_func: typing.Callable,
        log: logging.Logger,
    ) -> None:
        super().__init__(
            name=name,
            device_id=device_id,
            sensor=sensor,
            callback_func=callback_func,
            log=log,
        )

        # Default values that can be set by unit tests to modify the behavior
        # of the device:
        #    In the specific case of a temperature sensor, one or more channels
        #    can be physically disconnected which will make the sensor output a
        #    specific value for those channels. disconnected_channel makes the
        #    MockDevice mock one disconnected channel.
        self.disconnected_channel = -1
        #     When a connection to the sensor is established mid output, the
        #     telemetry for one or more channels is not received by the code.
        #     missed_channels mocks the number of channels that are missed
        #     because of that.
        self.missed_channels = 0
        #     The sensor produces an error (True) or not (False) when being
        #     read.
        self.in_error_state = False
        # Keep track of being open or not
        self.is_open = False
        # Buffer to "read" from
        self.telemetry_buffer = ""
        # Index of the last character returned from the buffer.
        self.last_index = 0
        # get event loop to run blocking tasks
        self.loop = asyncio.get_event_loop()

        # Registry of formatters for the different types of sensors.
        self.formatter_registry: typing.Dict[typing.Type[BaseSensor], MockFormatter] = {
            Hx85aSensor: MockHx85aFormatter(),
            Hx85baSensor: MockHx85baFormatter(),
            TemperatureSensor: MockTemperatureFormatter(),
        }

    async def basic_open(self) -> None:
        """Open the Sensor Device."""
        if not self.is_open:
            self.is_open = True
        else:
            self.log.info("Port already open!")

    async def readline(self) -> str:
        """Read a line of telemetry from the device.

        Returns
        -------
        line : `str`
            Line read from the device. Includes terminator string if there is
            one. May be returned empty if nothing was received or partial if
            the readline was started during device reception.
        """
        line: str = ""
        while not line.endswith(self.sensor.terminator):
            line += await self.loop.run_in_executor(None, self._read, 1)
        return line

    def _read(self, num_chars: int) -> str:
        """Mock an asynchronous read from a sensor.

        Parameters
        ----------
        num_chars : `int`
            The number of characters to return.

        Returns
        -------
        line : `str`
            A line of telemetry read from the sensor.
        """
        # Mock the time needed to output telemetry.
        time.sleep(0.01)

        # Mock a sensor that produces an error when being read.
        if self.in_error_state:
            return f"{self.sensor.terminator}"

        if self.telemetry_buffer == "":
            mock_formatter = self.formatter_registry[type(self.sensor)]
            channel_strs = mock_formatter.format_output(
                num_channels=self.sensor.num_channels,
                disconnected_channel=self.disconnected_channel,
                missed_channels=self.missed_channels,
            )

            # Reset self.missed_channels because truncated data only happens
            # when data is output when first connected. Note that a disconnect
            # followed by a connect will not reset the value of
            # missed_channels.
            self.missed_channels = 0
            self.telemetry_buffer = (
                self.sensor.delimiter.join(channel_strs) + self.sensor.terminator
            )
            self.last_index = 0

        end_index = self.last_index + num_chars
        if end_index > len(self.telemetry_buffer):
            end_index = len(self.telemetry_buffer)
        char = self.telemetry_buffer[self.last_index : end_index]
        self.last_index = end_index
        if self.last_index == len(self.telemetry_buffer):
            self.telemetry_buffer = ""

        return char

    async def basic_close(self) -> None:
        """Close the Sensor Device."""
        if self.is_open:
            self.is_open = False
        else:
            self.log.info("Port already closed.")
