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

__all__ = ["TcpipDataClient"]

import asyncio
import logging
import types
import typing

import yaml

from ..constants import Key
from ..device import TcpipDevice
from ..device_config import DeviceConfig
from ..processor import BaseProcessor
from .base_read_loop_data_client import BaseReadLoopDataClient
from .data_client_constants import sensor_dict, telemetry_processor_dict

if typing.TYPE_CHECKING:
    from lsst.ts import salobj


class TcpipDataClient(BaseReadLoopDataClient):
    """Get environmental data via TCP/IP.

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
        self.device_configuration: DeviceConfig | None = None
        self.processor: BaseProcessor | None = None

        super().__init__(
            config=config, topics=topics, log=log, simulation_mode=simulation_mode
        )
        self.configure()

        # Lock for TCP/IP communication
        self.stream_lock = asyncio.Lock()

        self.tcpip_device: TcpipDevice | None = None
        self.data: dict = {}
        self.data_event = asyncio.Event()

    @classmethod
    def get_config_schema(cls) -> dict[str, typing.Any]:
        return yaml.safe_load(
            """
$schema: http://json-schema.org/draft-07/schema#
description: Schema for TCP/IP sensors.
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
      Timeout for reading data from the sensor (sec).
    type: number
  max_read_timeouts:
    description: Maximum number of read timeouts before an exception is raised.
    type: integer
    default: 5
  name:
    description: Sensor name.
    type: string
  sensor_type:
    description: Type of the sensor.
    type: string
    enum:
    - CSAT3B
    - EFM100C
    - HX85A
    - HX85BA
    - LD250
    - Temperature
    - Windsonic
  channels:
    description: Number of channels.
    type: integer
  num_samples:
    description: >-
      Number of samples per telemetry sample. Only relevant for
      certain kinds of data, such as wind speed and direction.
      Ignored for other kinds of data.
    type: integer
    minimum: 2
    default: 60
  baud_rate:
    description: Baud rate of the sensor.
    type: integer
    default: 19200
  poll_interval:
    description: The poll interval between requests for the telemetry (sec).
    type: number
    default: 1.0
  location:
    description: Sensor location (used for all telemetry topics).
    type: string
required:
  - host
  - port
  - connect_timeout
  - read_timeout
  - max_read_timeouts
  - name
  - sensor_type
  - channels
  - num_samples
  - baud_rate
  - location
additionalProperties: false
"""
        )

    def configure(self) -> None:
        """Store the device configuration.

        This provides easy access when processing telemetry.
        """
        self.device_configuration = DeviceConfig(
            host=self.config.host,
            port=self.config.port,
            name=self.config.name,
            dev_type=None,
            dev_id=None,
            sens_type=self.config.sensor_type,
            num_channels=self.config.channels,
            num_samples=getattr(self.config, "num_samples", 0),
            baud_rate=self.config.baud_rate,
            location=self.config.location,
        )
        processor_type = telemetry_processor_dict[self.device_configuration.sens_type]
        self.processor = processor_type(
            self.device_configuration, self.topics, self.log
        )

    def descr(self) -> str:
        assert self.tcpip_device is not None
        return f"host={self.tcpip_device.host}, port={self.tcpip_device.port}"

    @property
    def connected(self) -> bool:
        return self.tcpip_device is not None and self.tcpip_device.connected

    async def connect(self) -> None:
        assert self.device_configuration is not None
        assert self.device_configuration.host is not None
        assert self.device_configuration.port is not None
        sensor_type = sensor_dict[self.device_configuration.sens_type]
        sensor = sensor_type(log=self.log, num_channels=self.config.channels)
        self.log.info(
            f"Opening TcpipDevice["
            f"host={self.device_configuration.host}, "
            f"port={self.device_configuration.port}, "
            f"{sensor_type=}]"
        )
        self.tcpip_device = TcpipDevice(
            name=self.config.name,
            host=self.device_configuration.host,
            port=self.device_configuration.port,
            sensor=sensor,
            baud_rate=0,
            callback_func=self.process_telemetry,
            log=self.log,
            simulation_mode=self.simulation_mode,
        )
        await self.tcpip_device.open()

    async def disconnect(self) -> None:
        self.log.debug("disconnect.")
        try:
            if self.connected:
                self.log.debug("Closing the tcpip_device.")
                assert self.tcpip_device is not None  # make mypy happy
                await self.tcpip_device.close()
        finally:
            self.tcpip_device = None

    async def process_telemetry(self, data: dict) -> None:
        self.log.debug(f"Received {data=}")
        self.data = data
        self.log.debug("Setting data_event.")
        self.data_event.set()

    async def read_data(self) -> None:
        """Read data.

        Notes
        -----
        This method needs to raise an `TimeoutError` when timing out,
        otherwise the `read_loop` method may hang forever.
        """
        self.log.debug("read_data")
        assert self.processor is not None
        async with asyncio.timeout(self.read_timeout):
            self.log.debug("Waiting for data_event to be set.")
            await self.data_event.wait()
        self.log.debug(f"Processing {self.data=}")
        telemetry_data = self.data[Key.TELEMETRY]
        timestamp = telemetry_data[Key.TIMESTAMP]
        response_code = telemetry_data[Key.RESPONSE_CODE]
        sensor_data = telemetry_data[Key.SENSOR_TELEMETRY]
        await self.processor.process_telemetry(timestamp, response_code, sensor_data)
        self.data_event.clear()
