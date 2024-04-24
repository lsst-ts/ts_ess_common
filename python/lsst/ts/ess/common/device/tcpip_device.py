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

__all__ = ["TcpipDevice"]

import asyncio
import logging
from typing import Any, Callable

from lsst.ts import tcpip, utils

from ..sensor import BaseSensor
from .base_device import BaseDevice
from .mock_device import MockDevice

# Timeout limit for communicating with the remote device (seconds). This
# includes writing a command and reading the response and reading telemetry.
# Unit tests can set this to a lower value to speed up the test.
COMMUNICATE_TIMEOUT = 60


class TcpipDevice(BaseDevice):
    """Remote device that publishes telemetry via TCP/IP.

    Parameters
    ----------
    name : `str`
        The name of the device.
    host : `str`
        The hostname of the device.
    port : `int`
        The port of the device.
    sensor : `BaseSensor`
        The sensor that produces the telemetry.
    baud_rate : `int`
        The baud rate of the sensor.
    callback_func : `Callable`
        Callback function to receive the telemetry.
    log : `logging.Logger`
        The logger to create a child logger for.
    simulation_mode : `int`
        Simulation mode; 0 for normal operation.
    """

    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        sensor: BaseSensor,
        baud_rate: int,
        callback_func: Callable,
        log: logging.Logger,
        simulation_mode: int,
    ) -> None:
        super().__init__(
            name=name,
            device_id="",
            sensor=sensor,
            baud_rate=baud_rate,
            callback_func=callback_func,
            log=log,
        )
        self.host = host
        self.port = port
        self.client: tcpip.Client = tcpip.Client(host="", port=0, log=log)

        self.simulation_mode = simulation_mode
        self.mock_remote_device: MockRemoteDevice | None = None

        # Lock for TCP/IP communication.
        self.stream_lock = asyncio.Lock()

    @property
    def connected(self) -> bool:
        return self.client is not None and self.client.connected

    async def basic_open(self) -> None:
        """Open the Sensor Device."""
        if self.connected:
            raise RuntimeError("Already connected.")

        if self.simulation_mode != 0:
            self.mock_remote_device = MockRemoteDevice(
                log=self.log, simulation_interval=1.0, sensor=self.sensor
            )
            await self.mock_remote_device.start_task
            self.host = self.mock_remote_device.host
            self.port = self.mock_remote_device.port

        self.client = tcpip.Client(
            host=self.host, port=self.port, log=self.log, name=type(self).__name__
        )
        await asyncio.wait_for(fut=self.client.start_task, timeout=COMMUNICATE_TIMEOUT)

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
        async with self.stream_lock:
            assert self.client is not None  # keep mypy happy.
            line = await asyncio.wait_for(
                self.client.readline(), timeout=COMMUNICATE_TIMEOUT
            )
        return line

    async def basic_close(self) -> None:
        """Close the Sensor Device."""
        if self.connected:
            assert self.client is not None  # make mypy happy
            await self.client.close()
            self.client = None


class MockRemoteDevice(tcpip.OneClientServer):
    def __init__(
        self,
        log: logging.Logger,
        simulation_interval: float,
        sensor: BaseSensor,
    ) -> None:
        super().__init__(
            host=tcpip.LOCALHOST_IPV4,
            port=0,
            log=log,
            connect_callback=self.connect_callback,
        )
        self.simulation_interval = simulation_interval
        self.write_loop_task = utils.make_done_future()
        self.mock_device = MockDevice(
            name="MockDevice",
            device_id="",
            sensor=sensor,
            callback_func=self._dummy_data_callback,
            log=log,
        )

    async def connect_callback(self, server: tcpip.OneClientServer) -> None:
        self.write_loop_task.cancel()
        if server.connected:
            self.write_loop_task = asyncio.create_task(self.write_loop())

    async def _dummy_data_callback(self, reply: dict[str, Any]) -> None:
        # Empty on purpose since it is never used.
        pass

    async def write_loop(self) -> None:
        line: str | None = None
        while self.connected:
            line = await self.mock_device.readline()
            await self.write(line.encode() + tcpip.DEFAULT_TERMINATOR)
            await asyncio.sleep(self.simulation_interval)
