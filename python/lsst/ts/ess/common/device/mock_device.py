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
import typing

from .base_device import BaseDevice
from .mock_formatter import MockFormatter
from .mock_hx85a_formatter import MockHx85aFormatter
from .mock_hx85ba_formatter import MockHx85baFormatter
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
    disconnected_channel : `int`, optional
        In the specific case of a temperature sensor, one or more channels
        can be physically disconnected which will make the sensor output a
        specific value for those channels. disconnected_channel makes the
        MockDevice mock one disconnected channel.
    missed_channels : `int`, optional
        When a connection to the sensor is established mid output, the
        telemetry for one or more channels is not received by the code.
        missed_channels mocks the number of channels that are missed because
        of that.
    in_error_state : `bool`, optional
        The sensor produces an error (True) or not (False) when being read.
    """

    def __init__(
        self,
        name: str,
        device_id: str,
        sensor: BaseSensor,
        callback_func: typing.Callable,
        log: logging.Logger,
        disconnected_channel: int = -1,
        missed_channels: int = 0,
        in_error_state: bool = False,
    ) -> None:
        super().__init__(
            name=name,
            device_id=device_id,
            sensor=sensor,
            callback_func=callback_func,
            log=log,
        )

        if -1 <= disconnected_channel < self.sensor.num_channels:
            self.disconnected_channel = disconnected_channel
        else:
            raise ValueError(
                f"disconnected_channel={disconnected_channel!r} should have a "
                f"value between 0 and {self.sensor.num_channels} or be None."
            )
        if 0 <= missed_channels <= self.sensor.num_channels:
            self.missed_channels = missed_channels
        else:
            raise ValueError(
                f"missed_channels={missed_channels!r} should have a value "
                f"between 0 and {self.sensor.num_channels}."
            )
        self.in_error_state = in_error_state

        # Registry of formatters for the different types of sensors.
        self.formatter_registry: typing.Dict[typing.Type[BaseSensor], MockFormatter] = {
            Hx85aSensor: MockHx85aFormatter(),
            Hx85baSensor: MockHx85baFormatter(),
            TemperatureSensor: MockTemperatureFormatter(),
        }

    async def basic_open(self) -> None:
        """Open the Sensor Device."""
        pass

    async def readline(self) -> str:
        """Read a line of telemetry from the device.

        Returns
        -------
        line : `str`
            Line read from the device. Includes terminator string if there is
            one. May be returned empty if nothing was received or partial if
            the readline was started during device reception.
        """
        # Mock the time needed to output telemetry.
        await asyncio.sleep(1)

        # Mock a sensor that produces an error when being read.
        if self.in_error_state:
            return f"{self.sensor.terminator}"

        mock_formatter = self.formatter_registry[type(self.sensor)]
        channel_strs = mock_formatter.format_output(
            num_channels=self.sensor.num_channels,
            disconnected_channel=self.disconnected_channel,
            missed_channels=self.missed_channels,
        )

        self.log.debug(f"channel_strs = {channel_strs}")

        # Reset self.missed_channels because truncated data only happens when
        # data is being output while connecting.
        self.missed_channels = 0
        return self.sensor.delimiter.join(channel_strs) + self.sensor.terminator

    async def basic_close(self) -> None:
        """Close the Sensor Device."""
        pass
