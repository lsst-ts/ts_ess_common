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

__all__ = ["GecThermalscannerProcessor"]

import logging
import types
from collections.abc import Sequence
from typing import TYPE_CHECKING

from ..device_config import DeviceConfig
from .base_processor import BaseProcessor

if TYPE_CHECKING:
    from lsst.ts import salobj


class GecThermalscannerProcessor(BaseProcessor):
    def __init__(
        self,
        device_configuration: DeviceConfig,
        topics: salobj.Controller | types.SimpleNamespace,
        log: logging.Logger,
    ) -> None:
        super().__init__(device_configuration, topics, log)

    async def process_telemetry(
        self,
        timestamp: float,
        response_code: int,
        sensor_data: Sequence[float | int | str],
    ) -> None:
        """Process GEC Instruments Thermalscanner sensor telemetry.

        Parameters
        ----------
        timestamp : `float`
            The timestamp of the data.
        response_code : `int`
            The ResponseCode
        sensor_data : each of type `float`
            A Sequence of floats representing 94 temperatures of the sensor.
        """
        await self.topics.tel_thermalScanner.set_write(temperatures=sensor_data)

        await self.topics.evt_sensorStatus.set_write(
            sensorName=self.device_configuration.name,
            sensorStatus=0,
            serverStatus=response_code,
        )
