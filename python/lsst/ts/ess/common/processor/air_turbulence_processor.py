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

__all__ = ["AirTurbulenceProcessor"]

import logging
import types
from collections.abc import Sequence
from typing import TYPE_CHECKING

from ..accumulator import AirTurbulenceAccumulator
from ..device_config import DeviceConfig
from .base_processor import BaseProcessor

if TYPE_CHECKING:
    from lsst.ts import salobj


class AirTurbulenceProcessor(BaseProcessor):
    def __init__(
        self,
        device_configuration: DeviceConfig,
        topics: salobj.Controller | types.SimpleNamespace,
        log: logging.Logger,
    ) -> None:
        super().__init__(device_configuration, topics, log)

        # Cache of data, a dict of sensor_name: AirTurbulenceAccumulator.
        self.air_turbulence_cache: dict[str, AirTurbulenceAccumulator] = dict()

    async def process_telemetry(
        self,
        timestamp: float,
        response_code: int,
        sensor_data: Sequence[float | int | str],
    ) -> None:
        """Process air turbulence telemetry.

        Accumulate a specified number of samples before writing
        the telemetry topic.

        Parameters
        ----------
        timestamp : `float`
            The timestamp of the data.
        response_code : `int`
            The ResponseCode.
        sensor_data : each of type `float` or `int`
            A Sequence of float and/or int representing the sensor telemetry
            data.
        """
        if self.device_configuration.name not in self.air_turbulence_cache:
            self.air_turbulence_cache[self.device_configuration.name] = AirTurbulenceAccumulator(
                log=self.log, num_samples=self.device_configuration.num_samples
            )

        isok = response_code == 0
        sensor_status = response_code
        if len(sensor_data) >= 5:
            isok = sensor_data[4] == 0 and response_code == 0
            sensor_status = int(sensor_data[4])
        accumulator = self.air_turbulence_cache[self.device_configuration.name]
        accumulator.add_sample(
            timestamp=timestamp,
            speed=sensor_data[0:3],  # type: ignore
            sonic_temperature=float(sensor_data[3]),
            isok=isok,
        )
        topic_kwargs = accumulator.get_topic_kwargs()
        if not topic_kwargs:
            return

        self.log.debug("Sending the tel_airTurbulence telemetry and evt_sensorStatus event.")
        await self.topics.tel_airTurbulence.set_write(
            sensorName=self.device_configuration.name,
            location=self.device_configuration.location,
            **topic_kwargs,
        )
        await self.topics.evt_sensorStatus.set_write(
            sensorName=self.device_configuration.name,
            sensorStatus=sensor_status,
            serverStatus=response_code,
        )
