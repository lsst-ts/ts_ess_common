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

__all__ = ["ControllerDataClient"]

import asyncio
import json
import logging
import types
import typing
from collections.abc import Sequence

import jsonschema
import yaml
from lsst.ts import tcpip

from ..constants import Command, DeviceType, Key, ResponseCode, SensorType
from ..device_config import DeviceConfig
from ..mock_command_handler import MockCommandHandler
from ..processor import BaseProcessor
from ..socket_server import SocketServer
from .base_read_loop_data_client import BaseReadLoopDataClient
from .data_client_constants import telemetry_processor_dict

if typing.TYPE_CHECKING:
    from lsst.ts import salobj


class ControllerDataClient(BaseReadLoopDataClient):
    """Get environmental data from sensors connected to an ESS Controller.

    Parameters
    ----------
    config : `types.SimpleNamespace`
        The configuration, after validation by the schema returned
        by `get_config_schema` and conversion to a types.SimpleNamespace.
    topics : `salobj.Controller` or `types.SimpleNamespace`
        The telemetry topics this data client can write,
        as a struct with attributes such as ``tel_temperature``.
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
        # Dict of sensor_name: device configuration.
        self.device_configurations: dict[str, DeviceConfig] = dict()

        # Lock for TCP/IP communication.
        self.stream_lock = asyncio.Lock()

        # TCP/IP Client.
        self.client: tcpip.Client | None = None

        # Set this attribute false before calling `start` to test failure
        # to connect to the server. Ignored if not simulating.
        self.enable_socket_server = True

        # Socket server for simulation mode.
        self.socket_server: SocketServer | None = None

        super().__init__(
            config=config, topics=topics, log=log, simulation_mode=simulation_mode
        )
        self.configure()

        # Validator for JSON data.
        self.validator = jsonschema.Draft7Validator(schema=self.get_telemetry_schema())

        # A dict of sensor_name: BaseProcessor.
        self.processors: dict[str, BaseProcessor] = dict()

    @classmethod
    def get_config_schema(cls) -> dict[str, typing.Any]:
        return yaml.safe_load(
            """
$schema: http://json-schema.org/draft-07/schema#
description: Schema for ControllerDataClient
type: object
properties:
  host:
    description: IP address of the TCP/IP interface.
    type: string
    format: hostname
  port:
    description: Port number of the TCP/IP interface.
    type: integer
    default: 5000
  max_read_timeouts:
    description: Maximum number of read timeouts before an exception is raised.
    type: integer
    default: 5
  connect_timeout:
    description: Timeout for connecting to the TCP/IP interface (sec).
    type: number
    default: 60.0
  rate_limit:
    type: number
    default: 0.5
  devices:
    type: array
    minItems: 1
    items:
      type: object
      properties:
        name:
          description: Name of the sensor.
          type: string
        sensor_type:
          description: Type of the sensor.
          type: string
          enum:
          - Aurora
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
        device_type:
          description: Type of the device.
          type: string
          enum:
          - FTDI
          - Serial
        baud_rate:
          description: Baud rate of the sensor.
          type: integer
          default: 19200
        location:
          description: >-
            The location of the device. In case of a multi-channel device with
            probes that can be far away from the sensor, a comma separated line
            can be used to give the location of each probe. In that case the
            locations should be given in the order of the channels.
          type: string
        safe_interval:
          description: >-
            The amount of time [s] after which an event is sent informing that
            no lightning strikes or high electric field have been detected
            anymore.
          type: integer
          default: 10
        num_samples:
          description: >-
            Number of samples per telemetry sample. Only relevant for
            certain kinds of data, such as wind speed and direction and
            electric field strength data Ignored for other kinds of data.
          type: integer
          minimum: 2
      anyOf:
      - if:
          properties:
            device_type:
              const: FTDI
        then:
          properties:
            ftdi_id:
              description: FTDI Serial ID to connect to.
              type: string
      - if:
          properties:
            device_type:
              const: Serial
        then:
          properties:
            serial_port:
              description: Serial port to connect to.
              type: string
      required:
        - name
        - sensor_type
        - device_type
        - baud_rate
        - location
required:
  - host
  - port
  - max_read_timeouts
  - connect_timeout
  - rate_limit
  - devices
additionalProperties: false
"""
        )

    @classmethod
    def get_telemetry_schema(cls) -> dict[str, typing.Any]:
        return json.loads(
            """
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "description": "Schema for Sensor Telemetry",
  "type": "object",
  "properties": {
    "telemetry": {
      "type": "object",
      "properties": {
        "name": {
          "description": "Name of the sensor.",
          "type": "string"
        },
        "timestamp": {
          "description": "Timestamp of the telemetry.",
          "type": "number"
        },
        "response_code": {
          "description": "Response code indicating if all is OK or if there is an error.",
          "type": "number"
        },
        "sensor_telemetry": {
          "description": "The sensor telemetry.",
          "type": "array",
          "minItems": 1
        }
      },
      "required": ["name", "timestamp", "response_code", "sensor_telemetry"],
      "additionalProperties": false
    }
  },
  "required": ["telemetry"],
  "additionalProperties": false
}
            """
        )

    @property
    def connected(self) -> bool:
        return self.client is not None and self.client.connected

    def configure(self) -> None:
        """Store device configurations.

        This provides easy access when processing telemetry.
        """
        for device in self.config.devices:
            if device[Key.DEVICE_TYPE] == DeviceType.FTDI:
                dev_id = Key.FTDI_ID
            elif device[Key.DEVICE_TYPE] == DeviceType.SERIAL:
                dev_id = Key.SERIAL_PORT
            else:
                raise RuntimeError(
                    f"Unknown device type {device[Key.DEVICE_TYPE]} encountered.",
                )
            num_channels = 0
            sensor_type = device[Key.SENSOR_TYPE]
            if sensor_type == SensorType.TEMPERATURE:
                num_channels = device[Key.CHANNELS]
            self.device_configurations[device[Key.NAME]] = DeviceConfig(
                name=device[Key.NAME],
                num_channels=num_channels,
                dev_type=device[Key.DEVICE_TYPE],
                dev_id=device[dev_id],
                sens_type=device[Key.SENSOR_TYPE],
                baud_rate=device[Key.BAUD_RATE],
                location=device.get(Key.LOCATION, "Location not specified."),
                num_samples=device.get(Key.NUM_SAMPLES, 0),
                safe_interval=device.get(Key.SAFE_INTERVAL, 0),
                threshold=device.get(Key.THRESHOLD, 0),
            )

    def descr(self) -> str:
        return f"host={self.config.host}, port={self.config.port}"

    async def connect(self) -> None:
        """Connect to the ESS Controller and configure it.

        Raises
        ------
        RuntimeError
            If already connected.
        """
        if self.connected:
            raise RuntimeError("Already connected.")

        if self.simulation_mode != 0:
            if self.enable_socket_server:
                self.socket_server = SocketServer(
                    name="SocketServer",
                    host=tcpip.DEFAULT_LOCALHOST,
                    port=0,
                    log=self.log,
                    simulation_mode=1,
                )
                assert self.socket_server is not None  # make mypy happy
                mock_command_handler = MockCommandHandler(
                    callback=self.socket_server.write_json,
                    simulation_mode=1,
                )
                self.socket_server.set_command_handler(mock_command_handler)
                async with asyncio.timeout(self.connect_timeout):
                    await self.socket_server.start_task
                # Change self.config instead of using a local variable
                # so descr and __repr__ show the correct host and port
                port = self.socket_server.port
            else:
                self.log.info(
                    f"{self}.enable_socket_server false; connection will fail."
                )
                port = 0
            # Change self.config so descr and __repr__ show the actual
            # host and port.
            self.config.host = tcpip.LOCAL_HOST
            self.config.port = port

        self.client = tcpip.Client(
            host=self.config.host,
            port=self.config.port,
            log=self.log,
            name=type(self).__name__,
        )
        async with asyncio.timeout(self.connect_timeout):
            await self.client.start_task
        configuration = {Key.DEVICES: self.config.devices}
        await self.run_command(command=Command.CONFIGURE, configuration=configuration)

    async def disconnect(self) -> None:
        """Disconnect from the ESS Controller.

        Always safe to call, though it may raise asyncio.CancelledError
        if the client is currently being closed.
        """
        if self.connected:
            assert self.client is not None  # make mypy happy
            await self.client.close()
            self.client = None
        if self.socket_server is not None:
            await self.socket_server.close()

    async def read_data(self) -> None:
        """Read and process data from the ESS Controller."""
        async with self.stream_lock:
            assert self.client is not None
            async with asyncio.timeout(self.read_timeout):
                data = await self.client.read_json()
        if Key.RESPONSE in data:
            self.log.warning("Read a command response with no command pending.")
        elif Key.TELEMETRY in data:
            self.log.debug(f"Processing {data}.")
            try:
                self.validator.validate(data)
                telemetry_data = data[Key.TELEMETRY]
                await self.process_telemetry(
                    sensor_name=telemetry_data[Key.NAME],
                    timestamp=telemetry_data[Key.TIMESTAMP],
                    response_code=telemetry_data[Key.RESPONSE_CODE],
                    sensor_data=telemetry_data[Key.SENSOR_TELEMETRY],
                )
            except Exception:
                self.log.exception(f"Exception processing {data}. Ignoring.")
        else:
            self.log.warning(f"Ignoring unparsable {data}.")

    async def run_command(self, command: str, **parameters: typing.Any) -> None:
        """Write a command. Time out if it takes too long.

        Parameters
        ----------
        command : `str`
            The command to write.
        **parameters : `dict`
            Command parameters, as name=dict. For example::

                configuration = {"devices": self.config.devices}

        Raises
        ------
        ConnectionError
            If not connected.
        TimeoutError
            If it takes more than COMMUNICATE_TIMEOUT seconds
            to acquire the lock or write the data.
        """
        data: dict[str, typing.Any] = {
            Key.COMMAND: command,
            Key.PARAMETERS: parameters,
        }
        async with asyncio.timeout(self.connect_timeout):
            await self._basic_run_command(data)

    async def _basic_run_command(self, data: dict[str, typing.Any]) -> None:
        """Write a json-encoded command dict. Potentially wait forever.

        Parameters
        ----------
        data : `dict`[`str`, `typing.Any`]
            The data to write. The data should be of the form (but this is not
            verified)::

                {"command": command_str, "parameters": params_dict}

        Raises
        ------
        RuntimeError
            If the command fails.
        ConnectionError
            If disconnected before command is acknowledged.
        """
        async with self.stream_lock:
            if not self.connected:
                raise ConnectionError("Not connected; cannot send the command.")
            assert self.client is not None
            await self.client.write_json(data)
            while True:
                if not self.connected:
                    raise ConnectionError(
                        "Disconnected while waiting for command response."
                    )
                data = await self.client.read_json()
                if Key.RESPONSE in data:
                    response = data[Key.RESPONSE]
                    if response == ResponseCode.OK:
                        return
                    else:
                        raise RuntimeError(f"Command {data!r} failed: {response=!r}.")
                else:
                    self.log.debug("Ignoring non-command-ack.")

    async def process_telemetry(
        self,
        sensor_name: str,
        timestamp: float,
        response_code: int,
        sensor_data: Sequence[float | int | str],
    ) -> None:
        """Process the sensor telemetry.

        Parameters
        ----------
        sensor_name : `str`
            The name of the sensor.
        timestamp : `float`
            The timestamp of the data.
        response_code : `int`
            The response code.
        sensor_data : each of type `float`
            A Sequence of float representing the sensor telemetry data.

        Raises
        ------
        RuntimeError
            If the response code is common.ResponseCode.DEVICE_READ_ERROR
        """
        try:
            device_configuration = self.device_configurations.get(sensor_name)
            if device_configuration is None:
                raise RuntimeError(
                    f"No device configuration for sensor_name={sensor_name}."
                )
            if response_code == ResponseCode.OK:
                if sensor_name not in self.processors:
                    processor_type = telemetry_processor_dict[
                        device_configuration.sens_type
                    ]
                    self.processors[sensor_name] = processor_type(
                        device_configuration, self.topics, self.log
                    )
                p = self.processors[sensor_name]
                await p.process_telemetry(timestamp, response_code, sensor_data)
            elif response_code == ResponseCode.DEVICE_READ_ERROR:
                raise RuntimeError(
                    f"Error reading sensor {sensor_name}. Please check the hardware."
                )
            else:
                self.log.warning(
                    f"Ignoring telemetry for sensor {sensor_name} "
                    f"with unknown response code {response_code}."
                )
        except Exception as e:
            self.log.exception(f"process_telemetry failed: {e!r}.")
            raise
