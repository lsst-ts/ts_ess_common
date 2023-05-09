# This file is part of ts_ess_dataclients.
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

__all__ = ["MockCommandHandler"]

from typing import Any

from .abstract_command_handler import AbstractCommandHandler
from .constants import Key
from .device import BaseDevice, MockDevice
from .sensor import create_sensor

MOCK_DEVICE_ID_PREFIX = "MockDevice"


class MockCommandHandler(AbstractCommandHandler):
    def create_device(self, device_configuration: dict[str, Any]) -> BaseDevice:
        """Create the device to connect to by using the specified
        configuration.

        Parameters
        ----------
        device_configuration : `dict`
            A dict representing the device to connect to. The format of the
            dict is described in the devices part of
            `lsst.ts.ess.dataclients.CONFIG_SCHEMA`.

        Returns
        -------
        device : `dataclients.device.BaseDevice`
            The device to connect to.

        Raises
        ------
        RuntimeError
            In case an incorrect configuration has been loaded.
        """
        sensor = create_sensor(device_configuration=device_configuration, log=self.log)
        self.log.debug(
            f"Creating MockDevice with name {device_configuration[Key.NAME]} and sensor {sensor}."
        )
        device: BaseDevice = MockDevice(
            name=device_configuration[Key.NAME],
            device_id=f"{MOCK_DEVICE_ID_PREFIX}-{device_configuration[Key.NAME]}",
            sensor=sensor,
            callback_func=self._callback,
            log=self.log,
        )
        return device
