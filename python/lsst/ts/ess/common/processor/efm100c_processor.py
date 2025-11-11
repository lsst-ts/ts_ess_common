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

__all__ = ["Efm100cProcessor"]

import asyncio
import logging
import types
from collections.abc import Sequence
from typing import TYPE_CHECKING

import numpy as np
from lsst.ts import utils

from ..accumulator import ElectricFieldStrengthAccumulator
from ..constants import ResponseCode
from ..device_config import DeviceConfig
from .base_processor import BaseProcessor

if TYPE_CHECKING:
    from lsst.ts import salobj


class Efm100cProcessor(BaseProcessor):
    def __init__(
        self,
        device_configuration: DeviceConfig,
        topics: salobj.Controller | types.SimpleNamespace,
        log: logging.Logger,
    ) -> None:
        super().__init__(device_configuration, topics, log)

        # Timer task to send a event when the electric field strength has
        # dropped below the configurable threshold for a configurable amount of
        # time.
        self.high_electric_field_timer_task = utils.make_done_future()

        # Cache of data, a dict of
        # sensor_name: ElectricFieldStrengthAccumulator.
        self.electric_field_strength_cache: dict[str, ElectricFieldStrengthAccumulator] = dict()

    async def process_telemetry(
        self,
        timestamp: float,
        response_code: int,
        sensor_data: Sequence[float | str | int],
    ) -> None:
        """Process EFM-100C electric field strength detector telemetry.

        Parameters
        ----------
        timestamp : `float`
            The timestamp of the data.
        response_code : `int`
            The ResponseCode.
        sensor_data : each of type `float`, `int` or `str`.
            A Sequence of float representing the sensor telemetry data.
        """
        if self.device_configuration.name not in self.electric_field_strength_cache:
            self.electric_field_strength_cache[self.device_configuration.name] = (
                ElectricFieldStrengthAccumulator(num_samples=self.device_configuration.num_samples)
            )
        accumulator = self.electric_field_strength_cache[self.device_configuration.name]

        accumulator.add_sample(
            timestamp=timestamp,
            strength=float(sensor_data[0]),
            isok=sensor_data[1] == 0 and response_code == ResponseCode.OK,
        )

        topic_kwargs = accumulator.get_topic_kwargs()
        if not topic_kwargs:
            return

        topic_kwargs["location"] = self.device_configuration.location
        if np.abs(topic_kwargs["strengthMax"]) > self.device_configuration.threshold:
            if not self.high_electric_field_timer_task.done():
                self.high_electric_field_timer_task.cancel()
            # Then start a new one so the safe time interval is reset.
            self.high_electric_field_timer_task = asyncio.create_task(
                asyncio.sleep(self.device_configuration.safe_interval)
            )
            self.log.debug("Sending the evt_highElectricField event.")
            await self.topics.evt_highElectricField.set_write(
                sensorName=self.device_configuration.name,
                strength=self.device_configuration.threshold,
            )
        else:
            if self.high_electric_field_timer_task.done():
                self.log.debug("Sending the evt_highElectricField event.")
                await self.topics.evt_highElectricField.set_write(
                    sensorName=self.device_configuration.name,
                    strength=np.nan,
                )
        self.log.debug("Sending the tel_electricFieldStrength telemetry and evt_sensorStatus event.")
        await self.topics.tel_electricFieldStrength.set_write(
            sensorName=self.device_configuration.name,
            **topic_kwargs,
        )
        await self.topics.evt_sensorStatus.set_write(
            sensorName=self.device_configuration.name,
            sensorStatus=sensor_data[1],
            serverStatus=response_code,
        )
