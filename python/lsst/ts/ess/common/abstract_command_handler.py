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

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

import jsonschema

from .command_error import CommandError
from .config_schema import CONFIG_SCHEMA
from .constants import Command, Key, ResponseCode
from .device import BaseDevice


class AbstractCommandHandler(ABC):
    """Handle incoming commands and send replies. Apply configuration and read
    sensor data.

    Parameters
    ----------
    callback : `Callable`
        The callback coroutine handling the sensor telemetry. This can be a
        coroutine that sends the data via a socket connection or a coroutine in
        a test class to verify that the command has been handled correctly.
    simulation_mode : `int`
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

    def __init__(self, callback: Callable, simulation_mode: int) -> None:
        self.log = logging.getLogger(type(self).__name__)
        if simulation_mode not in self.valid_simulation_modes:
            raise ValueError(
                f"simulation_mode={simulation_mode} "
                f"not in valid_simulation_modes={self.valid_simulation_modes}"
            )

        self.simulation_mode = simulation_mode

        self._callback = callback
        self.configuration: None | dict[str, Any] = None
        self._started = False

        self.devices: list[BaseDevice] = []

        self.dispatch_dict: dict[str, Callable] = {
            Command.CONFIGURE: self.configure,
        }

    async def handle_command(self, command: str, **kwargs: Any) -> None:
        """Handle incomming commands and parameters.

        Parameters
        ----------
        command : `str`
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

    def _validate_configuration(self, configuration: dict[str, Any]) -> None:
        """Validate the configuration.

        Parameters
        ----------
        configuration : `dict`
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

    async def configure(self, configuration: dict[str, Any]) -> None:
        """Apply the configuration and start sending telemetry.

        Parameters
        ----------
        configuration : `dict`
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
        self.configuration = configuration

        device_configurations = self.configuration[Key.DEVICES]
        self.devices = []
        for device_configuration in device_configurations:
            device: BaseDevice = self.create_device(device_configuration)
            self.devices.append(device)
            self.log.debug(
                f"Opening {device_configuration[Key.DEVICE_TYPE]} "
                f"device with name {device_configuration[Key.NAME]}"
            )
            await device.open()

        self._started = True

    async def stop_sending_telemetry(self) -> None:
        """Stop reading the sensor data.

        Raises
        ------
        `CommandError`
            A CommandError with ResponseCode NOT_STARTED is raised if the
            command handler was not started yet.
        """
        self.log.debug("stop_sending_telemetry")
        if not self._started:
            self.log.warning("Not started yet. Ignoring stop command.")
            return

        while self.devices:
            device: BaseDevice = self.devices.pop(-1)
            self.log.debug(f"Closing {device} device with name {device.name}")
            await device.close()

        self._started = False

    @abstractmethod
    def create_device(self, device_configuration: dict[str, Any]) -> BaseDevice:
        """Create the device to connect to by using the specified
        configuration.

        Parameters
        ----------
        device_configuration : `dict`
            A dict representing the device to connect to. The format of the
            dict follows the configuration of the ts_ess_csc project.

        Returns
        -------
        device : `common.device.BaseDevice`
            The device to connect to.

        Raises
        ------
        `RuntimeError`
            In case an incorrect configuration has been loaded.

        Notes
        -----
        In this case a MockDevice always is returned. Sub-classes should
        override this method to add support for other devices.
        """
        raise NotImplementedError
