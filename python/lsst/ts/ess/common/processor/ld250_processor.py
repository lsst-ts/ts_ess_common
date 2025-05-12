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

__all__ = ["Ld250Processor"]

import asyncio
import logging
import types
from collections.abc import Sequence
from typing import TYPE_CHECKING

import numpy as np
from lsst.ts import utils

from ..constants import LD250TelemetryPrefix
from ..device_config import DeviceConfig
from .base_processor import BaseProcessor

if TYPE_CHECKING:
    from lsst.ts import salobj


class Ld250Processor(BaseProcessor):
    def __init__(
        self,
        device_configuration: DeviceConfig,
        topics: salobj.Controller | types.SimpleNamespace,
        log: logging.Logger,
    ) -> None:
        super().__init__(device_configuration, topics, log)

        # Timer task to send an event when there have been no more lightning
        # strikes for a configurable amount of time.
        self.strike_timer_task = utils.make_done_future()

    async def process_telemetry(
        self,
        timestamp: float,
        response_code: int,
        sensor_data: Sequence[float | str | int],
    ) -> None:
        """Process LD-250 lightning detector telemetry.

        Parameters
        ----------
        timestamp : `float`
            The timestamp of the data.
        response_code : `int`
            The ResponseCode.
        sensor_data : each of type `float`, `int` or `str`.
            A Sequence of float representing the sensor telemetry data.
        """
        if sensor_data[0] == LD250TelemetryPrefix.STRIKE_PREFIX:
            await self.process_ld250_strike(sensor_data=sensor_data)
        elif sensor_data[0] in [
            LD250TelemetryPrefix.NOISE_PREFIX,
            LD250TelemetryPrefix.STATUS_PREFIX,
        ]:
            await self.process_ld250_noise_or_status(
                timestamp=timestamp,
                response_code=response_code,
                sensor_data=sensor_data,
            )
        else:
            self.log.error(f"Received unknown telemetry prefix {sensor_data[0]}.")

        # If the timer task is done, and not canceled, then the safe time
        # interval has passed without any new strikes and a "safe" event can be
        # sent.
        if self.strike_timer_task.done() and not self.strike_timer_task.cancelled():
            await self.topics.evt_lightningStrike.set_write(
                sensorName=self.device_configuration.name,
                correctedDistance=np.inf,
                uncorrectedDistance=np.inf,
                bearing=0,
            )

    async def process_ld250_strike(
        self, sensor_data: Sequence[float | str | int]
    ) -> None:
        # First cancel any running timer task.
        if not self.strike_timer_task.done():
            self.strike_timer_task.cancel()
        # Then start a new one so the safe time interval is reset.
        self.strike_timer_task = asyncio.create_task(
            asyncio.sleep(self.device_configuration.safe_interval)
        )
        await self.topics.evt_lightningStrike.set_write(
            sensorName=self.device_configuration.name,
            correctedDistance=float(sensor_data[1]),
            uncorrectedDistance=float(sensor_data[2]),
            bearing=float(sensor_data[3]),
        )

    async def process_ld250_noise_or_status(
        self,
        timestamp: float,
        response_code: int,
        sensor_data: Sequence[float | str | int],
    ) -> None:
        isok = response_code == 0
        sensor_status = 0

        close_strike_rate = np.nan
        total_strike_rate = np.nan
        close_alarm_status = False
        severe_alarm_status = False
        heading = np.nan
        if sensor_data[0] == LD250TelemetryPrefix.NOISE_PREFIX:
            sensor_status = 1
            isok = False
        if isok:
            close_strike_rate = float(sensor_data[1])
            total_strike_rate = float(sensor_data[2])
            close_alarm_status = sensor_data[3] == 0
            severe_alarm_status = sensor_data[4] == 0
            heading = float(sensor_data[5])

        topic_kwargs = {
            "sensorName": self.device_configuration.name,
            "timestamp": timestamp,
            "closeStrikeRate": close_strike_rate,
            "totalStrikeRate": total_strike_rate,
            "closeAlarmStatus": close_alarm_status,
            "severeAlarmStatus": severe_alarm_status,
            "heading": heading,
            "location": self.device_configuration.location,
        }
        await self.topics.tel_lightningStrikeStatus.set_write(**topic_kwargs)
        await self.topics.evt_sensorStatus.set_write(
            sensorName=self.device_configuration.name,
            sensorStatus=sensor_status,
            serverStatus=response_code,
        )
