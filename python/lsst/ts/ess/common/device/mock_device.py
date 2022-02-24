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
import concurrent
from io import BytesIO
import logging
import os
import pty
import threading
import time
import typing

import serial

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
        # Get event loop to run blocking tasks.
        self.loop = asyncio.get_event_loop()
        # Registry of formatters for the different types of sensors.
        self.formatter_registry: typing.Dict[typing.Type[BaseSensor], MockFormatter] = {
            Hx85aSensor: MockHx85aFormatter(),
            Hx85baSensor: MockHx85baFormatter(),
            TemperatureSensor: MockTemperatureFormatter(),
        }

        # Create a dummy serial port to mock a serial device.
        self.ser_port, self.client_port = pty.openpty()
        # Get the name of the client port to listen at.
        self.client_name = os.ttyname(self.client_port)
        # Open a pySerial connection to the client.
        self.ser = serial.Serial(port=self.client_name, baudrate=2400, timeout=10)
        # Thread that writes to the ser_port.
        self.write_thread = threading.Thread(target=self._write_loop)

    async def basic_open(self) -> None:
        """Open the Sensor Device."""
        if not self.ser.is_open:
            try:
                self.ser.open()
                self.log.info("Serial port opened.")
            except serial.SerialException as e:
                self.log.exception("Serial port open failed.")
                raise e
        else:
            self.log.info("Port already open!")
        self.write_thread.start()

    async def readline(self) -> str:
        """Read a line of telemetry from the device.

        Returns
        -------
        line : `str`
            Line read from the device. Includes terminator string if there is
            one. May be returned empty if nothing was received or partial if
            the readline was started during device reception.
        """
        buffer = BytesIO()
        terminator = self.sensor.terminator.encode(self.sensor.charset)
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            while not buffer.getvalue().endswith(terminator):
                buffer.write(await self.loop.run_in_executor(pool, self.ser.read, 1))
        return buffer.getvalue().decode(self.sensor.charset)

    def _write_loop(self) -> None:
        """Mock a serial sensor."""
        # Introduce a startup delay to mock connecting to a real sensor.
        time.sleep(1.0)
        while self.ser.is_open:
            # Mock a delay between the data outputs.
            time.sleep(0.1)

            # Mock a sensor that produces an error when being read.
            if self.in_error_state:
                telemetry_buffer = self.sensor.terminator
            else:
                mock_formatter = self.formatter_registry[type(self.sensor)]
                channel_strs = mock_formatter.format_output(
                    num_channels=self.sensor.num_channels,
                    disconnected_channel=self.disconnected_channel,
                    missed_channels=self.missed_channels,
                )

                # Reset self.missed_channels because truncated data only
                # happens when data is output when first connected. Note that a
                # disconnect followed by a connect will not reset the value of
                # missed_channels.
                self.missed_channels = 0
                telemetry_buffer = (
                    self.sensor.delimiter.join(channel_strs) + self.sensor.terminator
                )

            self.log.info(
                f"telemetry_buffer = {telemetry_buffer.encode(self.sensor.charset)!r}"
            )
            for c in telemetry_buffer:
                # Mock the time needed to output telemetry.
                time.sleep(0.05)
                os.write(self.ser_port, c.encode(self.sensor.charset))

    async def basic_close(self) -> None:
        """Close the Sensor Device."""
        if self.ser.is_open:
            self.ser.close()
            self.log.exception("Serial port closed.")
        else:
            self.log.info("Serial port already closed.")
