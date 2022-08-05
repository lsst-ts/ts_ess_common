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

__all__ = ["sensor_registry", "register_sensor", "create_sensor"]

import logging
from typing import Any, Type

from ..constants import Key, SensorType
from .base_sensor import BaseSensor

sensor_registry: dict[SensorType, Type[BaseSensor]] = dict()


def register_sensor(sensor_type: SensorType, sensor_class: Type[BaseSensor]) -> None:
    """Register a BaseSensor subclass against a SensorType.

    Parameters
    ----------
    sensor_type : `SensorType`
        The SensorType to register against.
    sensor_class : `Type`
        The BaseSensor subclass to register.

    Raises
    ------
    `TypeError`
        In case a class, that is not a subclass of BaseSensor, is registered.
    `ValueError`
        In case a SensorType already was registered.

    """
    if not issubclass(sensor_class, BaseSensor):
        raise TypeError(
            f"sensor_class={sensor_class!r} is not a subclass of BaseSensor."
        )
    if sensor_type in sensor_registry:
        raise ValueError(f"sensor_type={sensor_type} already registered.")
    sensor_registry[sensor_type] = sensor_class


def create_sensor(
    device_configuration: dict[str, Any], log: logging.Logger
) -> BaseSensor:
    """Create the sensor to connect to by using the specified
    configuration.

    Parameters
    ----------
    device_configuration : `dict`
            A dict representing the device to connect to. The format of the
            dict is described in the devices part of
            `lsst.ts.ess.common.CONFIG_SCHEMA`.
    log : `logging.Logger`
        The logger to pass on to the sensor.

    Returns
    -------
    sensor : `BaseSensor`
        The sensor to connect to.

    Raises
    ------
    `KeyError`
        In case the device configuration doesn't have the sensor type key or
        the sensor type is not present in the sensor registry.
    """

    sensor_type = device_configuration[Key.SENSOR_TYPE]
    sensor_class = sensor_registry[sensor_type]
    if Key.CHANNELS in device_configuration:
        num_channels = device_configuration[Key.CHANNELS]
        return sensor_class(log=log, num_channels=num_channels)
    else:
        return sensor_class(log=log)
