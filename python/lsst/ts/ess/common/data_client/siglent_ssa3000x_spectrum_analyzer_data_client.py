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

__all__ = ["SiglentSSA3000xSpectrumAnalyzerDataClient"]

import asyncio
import enum
import logging
import types
from typing import TYPE_CHECKING, Any

import numpy as np
import yaml
from astropy import units
from lsst.ts import tcpip, utils

from .base_read_loop_data_client import BaseReadLoopDataClient

if TYPE_CHECKING:
    from lsst.ts import salobj

# The standard TCP/IP line terminator (bytes).
TERMINATOR = b"\n"

# The expected number of data points as returned by the spectrum analyzer given
# the fixed start and stop frequency.
EXPECTED_NUMBER_OF_DATA_POINTS = 751

QUERY_TRACE_DATA_CMD = ":trace:data? 1"


class FreqUnit(enum.Enum):
    GHz = enum.auto()
    MHz = enum.auto()
    kHz = enum.auto()
    Hz = enum.auto()


class SiglentSSA3000xSpectrumAnalyzerDataClient(BaseReadLoopDataClient):
    """Get data from a Siglent SSA3000X Spectrum analyzer.

    Parameters
    ----------
    config : types.SimpleNamespace
        The configuration, after validation by the schema returned
        by `get_config_schema` and conversion to a types.SimpleNamespace.
    topics : `salobj.Controller` or `types.SimpleNamespace`
        The telemetry topics this data client can write,
        as a struct with attributes such as ``tel_spectrumAnalyzer``.
    log : `logging.Logger`
        Logger.
    simulation_mode : `int`, optional
        Simulation mode; 0 for normal operation.
    """

    def __init__(
        self,
        config: types.SimpleNamespace,
        topics: salobj.Controller | types.SimpleNamespace,
        log: logging.Logger,
        simulation_mode: int = 0,
    ) -> None:
        super().__init__(
            config=config, topics=topics, log=log, simulation_mode=simulation_mode
        )

        self.topics.tel_spectrumAnalyzer.set(
            sensorName=self.config.sensor_name, location=self.config.location
        )

        # Lock for TCP/IP communication
        self.stream_lock = asyncio.Lock()

        self.client: tcpip.Client | None = None
        self.mock_data_server: MockSiglentSSA3000xDataServer | None = None
        self._have_seen_data = False
        self.simulation_interval = 0.5

        self.start_frequency = 0.0
        self.stop_frequency = 0.0

    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        return yaml.safe_load(
            f"""
$schema: http://json-schema.org/draft-07/schema#
description: Schema for SiglentSSA3000xSpectrumAnalyzerDataClient
type: object
properties:
  host:
    description: Hostname of the TCP/IP interface.
    type: string
    format: hostname
  port:
    description: Port number of the TCP/IP interface.
    type: integer
    default: 5000
  connect_timeout:
    description: Timeout for connecting to the spectrum analyzer (sec).
    type: number
  read_timeout:
    description: >-
      Timeout for reading data from the spectrum analyzer (sec). Note that the
      standard output rate is 1 Hz.
    type: number
  max_read_timeouts:
    description: Maximum number of read timeouts before an exception is raised.
    type: integer
    default: 5
  location:
    description: Sensor location (used for all telemetry topics).
    type: string
  sensor_name:
    description: Spectrum Analyzer name.
    type: string
    default: SSA3000X
  poll_interval:
    description: The poll interval between requests for the scan telemetry (sec).
    type: number
    default: 1.0
  freq_start_value:
    description: Frequency to start scanning.
    type: number
    default: 0.0
  freq_start_unit:
    description: Units of the freq_start_value.
    type: string
    enum: {[e.name for e in FreqUnit]}
    default: GHz
  freq_stop_value:
    description: Frequency to end scanning.
    type: number
    default: 3.0
  freq_stop_unit:
    description: Units of the freq_stop_value.
    type: string
    enum: {[e.name for e in FreqUnit]}
    default: GHz
required:
  - host
  - port
  - connect_timeout
  - read_timeout
  - max_read_timeouts
  - location
  - sensor_name
  - poll_interval
additionalProperties: false
"""
        )

    def descr(self) -> str:
        assert self.client is not None  # keep mypy happy
        return f"host={self.client.host}, port={self.client.port}"

    def get_set_freq_start_cmd(
        self, start_freq: float, unit: FreqUnit = FreqUnit.GHz
    ) -> str:
        """Get the set start frequence command string for a given start
        frequency.

        Parameters
        ----------
        start_freq : `float`
            The scan start frequency. Unit will depend on the value of "unit"
            parameter.
        unit : `str`, optional
            Unit of the frequency parameter (GHz by default).

        Returns
        -------
        `str`
            String to be sent to the spectrum analyzer to select the start
            frequency.
        """
        command = f":frequency:start {start_freq:.1f} {unit.name}"
        self.log.info(f"frequency start command = {command}")
        return command

    def get_set_freq_stop_cmd(
        self, stop_freq: float, unit: FreqUnit = FreqUnit.GHz
    ) -> str:
        """Get the set stop frequence command string for a given stop
        frequency.

        Parameters
        ----------
        stop_freq : `float`
            The scan start frequency. Unit will depend on the value of "unit"
            parameter.
        unit : `str`, optional
            Unit of the frequency parameter (GHz by default).

        Returns
        -------
        `str`
            String to be sent to the spectrum analyzer to select the stop
            frequency.
        """
        command = f":frequency:stop {stop_freq:.1f} {unit.name}"
        self.log.info(f"frequency stop command = {command}")
        return command

    @property
    def connected(self) -> bool:
        return self.client is not None and self.client.connected

    async def connect(self) -> None:
        # The first data read from the spectrum analyzer can be truncated, in
        # which case that data may be discarded. This boolean is used to keep
        # track of having read data for the first time.
        self._have_seen_data = False

        if self.simulation_mode == 0:
            host = self.config.host
            port = self.config.port
        else:
            self.mock_data_server = MockSiglentSSA3000xDataServer(
                log=self.log, simulation_interval=self.simulation_interval
            )
            await self.mock_data_server.start_task
            host = tcpip.LOCALHOST_IPV4
            port = self.mock_data_server.port
            self.log.info(
                "Simulating output from an SSA3000X Spectrum Analyzer serial interface at "
                f"host={host}, port={port}."
            )

        self.client = tcpip.Client(host=host, port=port, log=self.log)
        await asyncio.wait_for(self.client.start_task, self.config.connect_timeout)

    async def disconnect(self) -> None:
        try:
            if self.connected:
                assert self.client is not None  # make mypy happy
                await self.client.close()
            if self.mock_data_server is not None:
                await self.mock_data_server.close()
                self.mock_data_server = None
        finally:
            self.client = None

    async def write(self, data: str) -> None:
        """Write the data appended with the standard terminator.

        Parameters
        ----------
        data : `str`
            The data to write.
        """
        assert self.client is not None  # make mypy happy
        await self.client.write(data.encode() + b"\r\n")

    async def setup_reading(self) -> None:
        self._have_seen_data = False
        if self.connected:
            await self.write(
                self.get_set_freq_start_cmd(
                    start_freq=self.config.freq_start_value,
                    unit=getattr(units, self.config.freq_start_unit),
                )
            )
            await self.write(
                self.get_set_freq_stop_cmd(
                    stop_freq=self.config.freq_stop_value,
                    unit=getattr(units, self.config.freq_stop_unit),
                )
            )
            self.start_frequency = float(
                await self.send_command_and_read_reply(":frequency:start?")
            )
            self.stop_frequency = float(
                await self.send_command_and_read_reply(":frequency:stop?")
            )
            assert self.client is not None
            self.log.info(
                f"SpectrumAnalyzer {self.client.host} has "
                f"{self.start_frequency=} and {self.stop_frequency=}"
            )

    async def read_data(self) -> None:
        """Read raw data from the SSA3000X Spectrum Analyzer."""
        timestamp = utils.current_tai()
        raw_data = await self.send_command_and_read_reply(QUERY_TRACE_DATA_CMD)
        raw_data_items = raw_data.split(",")
        # The data from the spectrum analyzer ends in a "," so the last item
        # will be an empty string and needs to be dropped.
        if raw_data_items[-1] == "":
            del raw_data_items[-1]
        data = [float(i.strip()) for i in raw_data_items]
        if len(data) < EXPECTED_NUMBER_OF_DATA_POINTS and not self._have_seen_data:
            logging.warning(
                f"Data of length {len(data)} read. Ignoring because this is the first time data was read."
            )
            self._have_seen_data = True
        elif len(data) != EXPECTED_NUMBER_OF_DATA_POINTS:
            raise RuntimeError(
                f"Encountered {len(data)} data points instead of "
                f"{EXPECTED_NUMBER_OF_DATA_POINTS}. Check the Spectrum "
                f"Analyzer and the configuration."
            )
        else:
            try:
                await self.topics.tel_spectrumAnalyzer.set_write(
                    startFrequency=self.start_frequency,
                    stopFrequency=self.stop_frequency,
                    spectrum=data,
                    timestamp=timestamp,
                )
            except Exception as e:
                self.log.exception(f"Failed to handle {data=}: {e!r}")

        await asyncio.sleep(self.config.poll_interval)

    async def send_command_and_read_reply(self, command: str) -> str:
        """Send a command and read the reply.

        Parameters
        ----------
        command : `str`
            The command to send.

        Returns
        -------
        str
            The reply.

        """
        await self.write(command)
        assert self.client is not None  # make mypy happy
        try:
            async with asyncio.timeout(self.read_timeout):
                read_bytes = await self.client.readuntil(TERMINATOR)
        except Exception:
            self._have_seen_data = False
            raise
        raw_data = read_bytes.decode().strip()
        return raw_data


class MockSiglentSSA3000xDataServer(tcpip.OneClientReadLoopServer):
    """Mock Siglent SSA3000x data server.

    Parameters
    ----------
    log : `logging.Logger`
        Logger.
    simulation_interval : `float`
        Interval between writes (sec).
    """

    def __init__(
        self,
        log: logging.Logger,
        simulation_interval: float,
    ) -> None:
        super().__init__(
            host=tcpip.LOCALHOST_IPV4,
            port=0,
            log=log,
        )
        self.simulation_interval = simulation_interval
        self.write_loop_task = utils.make_done_future()
        self.start_frequency = 0.0
        self.stop_frequency = 0.0

    async def read_and_dispatch(self) -> None:
        command = await self.read_str()
        self.log.info(f"{command=}")
        if command.startswith(":frequency:start "):
            self.start_frequency = await self.get_frequency_as_value(command[17:])
        elif command.startswith(":frequency:stop "):
            self.stop_frequency = await self.get_frequency_as_value(command[16:])
        elif command.startswith(":frequency:start?"):
            await self.write_str(f"{self.start_frequency}")
        elif command.startswith(":frequency:stop?"):
            await self.write_str(f"{self.stop_frequency}")
        elif command == QUERY_TRACE_DATA_CMD:
            await asyncio.sleep(self.simulation_interval)
            rng = np.random.default_rng(10)
            data = -100.0 * rng.random(EXPECTED_NUMBER_OF_DATA_POINTS)
            data_string = ", ".join(f"{d:0.3f}" for d in data)
            await self.write_str(data_string)

    async def get_frequency_as_value(self, frequency_str: str) -> float:
        frequency_items = frequency_str.split(" ")
        return (
            (float(frequency_items[0]) * getattr(units, frequency_items[1]))
            .to(units.Hz)
            .value
        )
