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

__all__ = ["DeviceConfig"]

import dataclasses

from .constants import DeviceType, Key, SensorType


@dataclasses.dataclass
class DeviceConfig:
    """Configuration for a device.

    Parameters
    ----------
    name : `str`
        The name of the device.
    dev_type : `DeviceType`
        The type of device.
    dev_id : `str`
        The ID of the device.
    sens_type : `SensorType`
        The type of sensor.
    baud_rate : `int`
        The baud rate of the sensor.
    location: `str`
        The location of the device.
    num_channels : `int`, optional
        The number of channels the output data, or 0 indicating that the number
        of channels is not configurable for this type of device. Defaults to 0.
    num_samples : `int`, optional
        The number of samples to accumulate before reporting telemetry.
        Only relevant for sensors that report statistics, such as anemometers.
        For those sensors the value must be > 1, and preferably larger.
        For other sensors use the default value of 0.
    safe_interval : `int`, optional
        The number of seconds to sleep before an event is sent indicating that
        a previously sent event is over. Defaults to 0.
    threshold : `float`, optional
        A threshold value that can be used to, for instance, determine if an
        event needs to be sent. Defaults to 0.0.
    """

    name: str
    dev_type: DeviceType
    dev_id: str
    sens_type: SensorType
    baud_rate: int
    location: str
    num_channels: int = 0
    num_samples: int = 0
    safe_interval: int = 0
    threshold: float = 0.0

    def __post_init(self) -> None:
        self.dev_type = DeviceType(self.dev_type)
        self.sens_type = SensorType(self.sens_type)

    def as_dict(self) -> dict[str, str | int]:
        """Return a dict with the instance attributes and their values as
        key-value pairs.

        Returns
        -------
        device_config_as_dict : `dict`
            A dictionary of key-value pairs representing the instance
            attributes and their values.
        """
        device_config_as_dict: dict[str, str | int] = {
            Key.NAME: self.name,
            Key.DEVICE_TYPE: self.dev_type,
            Key.SENSOR_TYPE: self.sens_type,
            Key.BAUD_RATE: self.baud_rate,
            Key.LOCATION: self.location,
        }

        # FTDI devices have an FTDI ID and Serial devices have a serial port.
        if self.dev_type == DeviceType.FTDI:
            device_config_as_dict[Key.FTDI_ID] = self.dev_id
        elif self.dev_type == DeviceType.SERIAL:
            device_config_as_dict[Key.SERIAL_PORT] = self.dev_id
        else:
            raise ValueError(f"Received unknown DeviceType {self.dev_type}")

        # Only temperature sensors have a configurable number of channels.
        if self.sens_type == SensorType.TEMPERATURE:
            device_config_as_dict[Key.CHANNELS] = self.num_channels
        return device_config_as_dict
