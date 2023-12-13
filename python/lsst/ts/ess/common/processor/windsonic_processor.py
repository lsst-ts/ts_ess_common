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

__all__ = ["WindsonicProcessor"]

import logging
import types
from collections.abc import Sequence
from typing import TYPE_CHECKING

from ..accumulator import AirFlowAccumulator
from ..constants import ResponseCode
from ..device_config import DeviceConfig
from .base_processor import BaseProcessor

if TYPE_CHECKING:
    from lsst.ts import salobj


class WindsonicProcessor(BaseProcessor):
    def __init__(
        self,
        device_configuration: DeviceConfig,
        topics: salobj.Controller | types.SimpleNamespace,
        log: logging.Logger,
    ) -> None:
        super().__init__(device_configuration, topics, log)

        # Cache of data, a dict of sensor_name: AirFlowAccumulator.
        self.air_flow_cache: dict[str, AirFlowAccumulator] = dict()

    async def process_telemetry(
        self,
        timestamp: float,
        response_code: int,
        sensor_data: Sequence[float | int | str],
    ) -> None:
        """Process Gill Windsonic sensor telemetry.

        Parameters
        ----------
        timestamp : `float`
            The timestamp of the data.
        response_code : `int`
            The ResponseCode
        sensor_data : each of type `float`
            A Sequence of floats representing the sensor telemetry data:

            * wind speed (m/s)
            * wind direction (deg)
        """
        if self.device_configuration.name not in self.air_flow_cache:
            self.air_flow_cache[self.device_configuration.name] = AirFlowAccumulator(
                log=self.log, num_samples=self.device_configuration.num_samples
            )
        accumulator = self.air_flow_cache[self.device_configuration.name]

        accumulator.add_sample(
            timestamp=timestamp,
            speed=float(sensor_data[0]),
            direction=float(sensor_data[1]),
            isok=response_code == ResponseCode.OK,
        )

        topic_kwargs = accumulator.get_topic_kwargs()
        if not topic_kwargs:
            return

        await self.topics.tel_airFlow.set_write(
            sensorName=self.device_configuration.name,
            location=self.device_configuration.location,
            **topic_kwargs,
        )
        await self.topics.evt_sensorStatus.set_write(
            sensorName=self.device_configuration.name,
            sensorStatus=0,
            serverStatus=response_code,
        )
