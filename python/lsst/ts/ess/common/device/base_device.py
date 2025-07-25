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

from __future__ import annotations

import asyncio
import logging
import types
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Type

from lsst.ts import utils

from ..constants import Key, ResponseCode
from ..sensor import BaseSensor

__all__ = ["BaseDevice"]

# Telemetry loop finish timeout [s].
TELEMETRY_LOOP_FINISH_TIMEOUT = 5.0

# Read timeout [seconds].
READ_TIMEOUT = 5.0

# Error state sleep time [sec].
ERROR_STATE_SLEEP_TIME = 0.1


class BaseDevice(ABC):
    """Base class for the different types of Sensor Devices.

    This class holds all common code for the hardware devices. Device specific
    code (for instance for a serial or an FTDI device) needs to be implemented
    in a subclass.

    Parameters
    ----------
    name : `str`
        The name of the device.
    device_id : `str`
        The hardware device ID to connect to. This can be a physical ID (e.g.
        /dev/ttyUSB0), a serial port (e.g. serial_ch_1) or any other ID used by
        the specific device.
    sensor : `BaseSensor`
        The sensor that produces the telemetry.
    baud_rate : `int`
        The baud rate of the sensor.
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
        baud_rate: int,
        callback_func: Callable,
        log: logging.Logger,
    ) -> None:
        self.name = name
        self.device_id = device_id
        self.sensor = sensor
        self.baud_rate = baud_rate
        self._callback_func = callback_func
        self._telemetry_loop = utils.make_done_future()
        self.loop_should_end = False
        self.is_open = False
        self.open_event = asyncio.Event()
        self.readline_event = asyncio.Event()
        self.log = log.getChild(type(self).__name__)

        # Support MockDevice fault state. To be used in unit tests only.
        self.in_error_state: bool = False

    async def __aenter__(self) -> BaseDevice:
        await self.open()
        return self

    async def __aexit__(
        self,
        type: None | Type[BaseException],
        value: None | BaseException,
        traceback: None | types.TracebackType,
    ) -> None:
        await self.close()

    def __repr__(self) -> str:
        vars_str = ", ".join(
            f"{var}={val!r}"
            for var, val in vars(self).items()
            if var not in {"log", "terminator"}
        )
        st = f"{type(self).__name__}<{vars_str}>"
        return st

    async def open(self) -> None:
        """Generic open function.

        Check if the device is open and, if not, call basic_open. Then start
        the telemetry loop.

        Raises
        ------
        RuntimeError
            In case the device already is open.
        """
        self.loop_should_end = False
        self.open_event.clear()
        self._telemetry_loop = asyncio.create_task(self._run())
        await self.open_event.wait()

    @abstractmethod
    async def basic_open(self) -> None:
        """Open the Sensor Device."""
        raise NotImplementedError()

    async def _run(self) -> None:
        """Run sensor read loop.

        If enabled, loop and read the sensor and pass result to callback_func.
        """
        self.log.debug(f"Starting read loop for {self.name!r} sensor.")
        self.open_event.clear()
        while not self.loop_should_end:
            try:
                if not self.is_open:
                    self.log.debug("Trying to open.")
                    await self.basic_open()
                    self.is_open = True
                    self.open_event.set()
                self.log.debug(f"{self.is_open=}, {self.loop_should_end=}")
                self.readline_event.clear()
                while self.is_open and not self.loop_should_end:
                    curr_tai = utils.current_tai()
                    response = ResponseCode.DEVICE_READ_ERROR
                    line = f"{self.sensor.terminator}"
                    if not self.in_error_state:
                        try:
                            async with asyncio.timeout(READ_TIMEOUT):
                                line = await self.readline()
                                response = ResponseCode.OK
                                self.readline_event.set()
                        except BaseException as e:
                            await self.handle_readline_exception(e)
                    else:
                        await asyncio.sleep(ERROR_STATE_SLEEP_TIME)

                    sensor_telemetry = await self.sensor.extract_telemetry(line=line)
                    reply = {
                        Key.TELEMETRY: {
                            Key.NAME: self.name,
                            Key.TIMESTAMP: curr_tai,
                            Key.RESPONSE_CODE: response,
                            Key.SENSOR_TELEMETRY: sensor_telemetry,
                        }
                    }
                    await self._callback_func(reply)
            except asyncio.CancelledError:
                self.loop_should_end = True
            finally:
                self.log.debug("finally...")
                self.open_event.clear()
                await self.basic_close()
                self.is_open = False

    async def handle_readline_exception(self, exception: BaseException) -> None:
        """Handle any exception that happened in the `readline` method.

        The default is to log and ignore but subclasses may override this
        method to customize the behavior.

        Parameters
        ----------
        exception : `BaseException`
            The exception to handle.
        """
        self.log.exception(f"Exception reading device {self.name}. Continuing.")

    @abstractmethod
    async def readline(self) -> str:
        """Read a line of telemetry from the device.

        Returns
        -------
        line : `str`
            Line read from the device. Includes terminator string if there is
            one. May be returned empty if nothing was received or partial if
            the readline was started during device reception.
        """
        raise NotImplementedError()

    async def close(self) -> None:
        """Stop the telemetry loop."""
        self.log.debug(f"Stopping read loop for {self.name!r} sensor.")
        self.loop_should_end = True

        try:
            async with asyncio.timeout(TELEMETRY_LOOP_FINISH_TIMEOUT):
                await self._telemetry_loop
        except TimeoutError:
            self.log.exception("Failed to close telemetry loop in time alloted.")
        except (Exception, asyncio.CancelledError):
            self.log.exception("Something went wrong so closing telemetry loop.")
        finally:
            notyet_cancelled = self._telemetry_loop.cancel()
            if notyet_cancelled:
                await self._telemetry_loop

    @abstractmethod
    async def basic_close(self) -> None:
        """Close the Sensor Device."""
        raise NotImplementedError()
