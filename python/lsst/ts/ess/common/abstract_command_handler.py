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

__all__ = ["AbstractCommandHandler"]

from abc import ABC, abstractmethod
import logging
import typing

import jsonschema

from .command_error import CommandError
from .config_schema import CONFIG_SCHEMA
from .constants import Command, Key, ResponseCode


class AbstractCommandHandler(ABC):
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

    valid_simulation_modes = (0, 1)

    @abstractmethod
    def __init__(self, callback: typing.Callable, simulation_mode: int) -> None:
        self.log = logging.getLogger(type(self).__name__)
        if simulation_mode not in self.valid_simulation_modes:
            raise ValueError(
                f"simulation_mode={simulation_mode} "
                f"not in valid_simulation_modes={self.valid_simulation_modes}"
            )

        self.simulation_mode = simulation_mode

        self._callback = callback
        self._configuration: typing.Optional[typing.Dict[str, typing.Any]] = None
        self._started = False

        self.dispatch_dict: typing.Dict[str, typing.Callable] = {
            Command.CONFIGURE: self.configure,
            Command.START: self.start_sending_telemetry,
            Command.STOP: self.stop_sending_telemetry,
        }

    async def handle_command(self, command: str, **kwargs: typing.Any) -> None:
        """Handle incomming commands and parameters.

        Parameters
        ----------
        command: `str`
            The command to handle.
        kwargs:
            The parameters to the command.
        """
        self.log.info(f"Handling command {command} with kwargs {kwargs}")
        func = self.dispatch_dict[command]
        try:
            await func(**kwargs)
            response = {Key.RESPONSE: ResponseCode.OK}
        except CommandError as e:
            self.log.exception("Encountered a CommandError.")
            response = {Key.RESPONSE: e.response_code}
        except Exception:
            self.log.exception(f"Command {command}({kwargs}) failed")
            raise
        await self._callback(response)

    def _validate_configuration(
        self, configuration: typing.Dict[str, typing.Any]
    ) -> None:
        """Validate the configuration.

        Parameters
        ----------
        configuration: `dict`
            A dict representing the configuration. The format of the dict
            follows the configuration of the ts_ess project.

        Raises
        ------
        `CommandError`:
            In case the provided configuration is incorrect.

        """

        try:
            jsonschema.validate(configuration, CONFIG_SCHEMA)
        except jsonschema.exceptions.ValidationError as e:
            raise CommandError(
                msg=f"Invalid configuration {e.message}.",
                response_code=ResponseCode.INVALID_CONFIGURATION,
            )

    async def configure(self, configuration: typing.Dict[str, typing.Any]) -> None:
        """Apply the configuration.

        Parameters
        ----------
        configuration: `dict`
            The contents of the dict depend on the type of sensor. See the
            ts_ess configuration schema for more details.

        Raises
        ------
        `CommandError`
            A CommandError with ResponseCode ALREADY_STARTED is raised if the
            command handler already was started.
        """
        self.log.info(f"configure with configuration data {configuration}")
        if self._started:
            raise CommandError(
                msg="Ignoring the configuration because telemetry loop already running. Send a stop first.",
                response_code=ResponseCode.ALREADY_STARTED,
            )
        self._validate_configuration(configuration=configuration)

        self._configuration = configuration

    async def start_sending_telemetry(self) -> None:
        """Connect the sensors and start reading the sensor data.

        Raises
        ------
        `CommandError`
            A CommandError with ResponseCode NOT_CONFIGURED is raised if the
            command handler was not configured yet.
        """
        self.log.info("start_sending_telemetry")
        if not self._configuration:
            raise CommandError(
                msg="No configuration has been received yet. Ignoring start command.",
                response_code=ResponseCode.NOT_CONFIGURED,
            )
        await self.connect_devices()
        self._started = True

    @abstractmethod
    async def connect_devices(self) -> None:
        """Loop over the configuration and start all devices."""
        raise NotImplementedError

    async def stop_sending_telemetry(self) -> None:
        """Stop reading the sensor data.

        Raises
        ------
        `CommandError`
            A CommandError with ResponseCode NOT_STARTED is raised if the
            command handler was not started yet.
        """
        self.log.info("stop_sending_telemetry")
        if not self._started:
            raise CommandError(
                msg="Not started yet. Ignoring stop command.",
                response_code=ResponseCode.NOT_STARTED,
            )
        await self.disconnect_devices()
        self._started = False

    @abstractmethod
    async def disconnect_devices(self) -> None:
        """Loop over the configuration and start all devices."""
        raise NotImplementedError