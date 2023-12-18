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

from __future__ import annotations

__all__ = ["BaseProcessor"]

import abc
import logging
import types
from collections.abc import Sequence
from typing import TYPE_CHECKING

from ..device_config import DeviceConfig

if TYPE_CHECKING:
    from lsst.ts import salobj


class BaseProcessor(abc.ABC):
    """Base class for telemetry processors.

    Parameters
    ----------
    device_configuration : `common.Deviceconfig`
        The configuration for the device.
    topics : `salobj.Controller` or `types.SimpleNamespace`
        The telemetry topics this data client can write,
        as a struct with attributes such as ``tel_temperature``.
    log : `logging.Logger`
        Logger.
    """

    def __init__(
        self,
        device_configuration: DeviceConfig,
        topics: salobj.Controller | types.SimpleNamespace,
        log: logging.Logger,
    ) -> None:
        self.device_configuration = device_configuration
        self.topics = topics
        self.log = log.getChild(type(self).__name__)

    @abc.abstractmethod
    async def process_telemetry(
        self,
        timestamp: float,
        response_code: int,
        sensor_data: Sequence[float | str | int],
    ) -> None:
        """Process telemetry.

        Parameters
        ----------
        timestamp : `float`
            The timestamp of the data.
        response_code : `int`
            The ResponseCode.
        sensor_data : each of type `float`
            A Sequence of float representing the sensor telemetry data.
        """
        raise NotImplementedError()
