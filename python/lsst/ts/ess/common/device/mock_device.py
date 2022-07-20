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
from collections.abc import Callable
import logging
from typing import Type

from .base_device import BaseDevice
from .mock_csat3b_formatter import MockCsat3bFormatter
from .mock_formatter import MockFormatter
from .mock_hx85_formatter import MockHx85aFormatter, MockHx85baFormatter
from .mock_temperature_formatter import MockTemperatureFormatter
from ..sensor import (
    BaseSensor,
    Csat3bSensor,
    Hx85aSensor,
    Hx85baSensor,
    TemperatureSensor,
)


class MockDevice(BaseDevice):
    # The wait time between sending telemetry (second). This can be adjusted by
    # unit tests to mock connection timeouts.
    telemetry_interval = 1

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
        callback_func: Callable,
        log: logging.Logger,
    ) -> None:
        super().__init__(
            name=name,
            device_id=device_id,
            sensor=sensor,
            baud_rate=19600,
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

        # Registry of formatters for the different types of sensors.
        self.formatter_registry: dict[Type[BaseSensor], MockFormatter] = {
            Csat3bSensor: MockCsat3bFormatter(),
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
        await asyncio.sleep(MockDevice.telemetry_interval)

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
        # data is output when first connected. Note that a disconnect followed
        # by a connect will not reset the value of missed_channels.
        self.missed_channels = 0
        return self.sensor.delimiter.join(channel_strs) + self.sensor.terminator

    async def basic_close(self) -> None:
        """Close the Sensor Device."""
        pass
