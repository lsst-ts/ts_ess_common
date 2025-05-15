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

__all__ = ["Sps30Processor"]

import logging
import types
from collections.abc import Sequence
from typing import TYPE_CHECKING

import numpy as np

from ..device_config import DeviceConfig
from .base_processor import BaseProcessor

if TYPE_CHECKING:
    from lsst.ts import salobj


class Sps30Processor(BaseProcessor):
    """Processor for SPS30 particulate matter sensor data."""

    def __init__(
        self,
        device_configuration: DeviceConfig,
        topics: salobj.Controller | types.SimpleNamespace,
        log: logging.Logger,
    ) -> None:
        """Initialize the processor.

        Parameters
        ----------
        device_configuration : `DeviceConfig`
            The device configuration.
        topics : `salobj.Controller` or `types.SimpleNamespace`
            The topics to write to.
        log : `logging.Logger`
            The logger to use for logging messages.
        """
        super().__init__(device_configuration, topics, log)

    async def process_telemetry(
        self,
        timestamp: float,
        response_code: int,
        sensor_data: Sequence[float | str | int],
    ) -> None:
        """Process SPS30 particulate matter sensor telemetry.

        Parameters
        ----------
        timestamp : `float`
            The timestamp of the data.
        response_code : `int`
            The ResponseCode.
        sensor_data : each of type `float`, `int` or `str`.
            A Sequence representing the sensor telemetry data.
        """
        isok = response_code == 0
        sensor_status = 0 if isok else 1

        # Initialize all values to NaN or False
        particle_sizes = {
            "pm1.0": np.nan,
            "pm2.5": np.nan,
            "pm4.0": np.nan,
            "pm10": np.nan,
            "pm_total": np.nan,
        }
        mass_concentrations = {
            "pm1.0": np.nan,
            "pm2.5": np.nan,
            "pm4.0": np.nan,
            "pm10": np.nan,
            "pm_total": np.nan,
        }
        number_concentrations = {
            "pm0.5": np.nan,
            "pm1.0": np.nan,
            "pm2.5": np.nan,
            "pm4.0": np.nan,
            "pm10": np.nan,
        }
        typical_particle_size = np.nan

        if isok and len(sensor_data) >= 19:
            try:
                particle_sizes = {
                    "pm1.0": float(sensor_data[2]),
                    "pm2.5": float(sensor_data[3]),
                    "pm4.0": float(sensor_data[4]),
                    "pm10": float(sensor_data[5]),
                    "pm_total": float(sensor_data[6]),
                }
                mass_concentrations = {
                    "pm1.0": float(sensor_data[7]),
                    "pm2.5": float(sensor_data[8]),
                    "pm4.0": float(sensor_data[9]),
                    "pm10": float(sensor_data[10]),
                    "pm_total": float(sensor_data[11]),
                }
                number_concentrations = {
                    "pm0.5": float(sensor_data[12]),
                    "pm1.0": float(sensor_data[13]),
                    "pm2.5": float(sensor_data[14]),
                    "pm4.0": float(sensor_data[15]),
                    "pm10": float(sensor_data[16]),
                }
                typical_particle_size = float(sensor_data[17])
            except (ValueError, IndexError) as e:
                self.log.error(f"Error processing SPS30 data: {e}")
                sensor_status = 1

        await self.topics.tel_particulateMatter.set_write(
            sensorName=self.device_configuration.name,
            timestamp=timestamp,
            particleSizes=particle_sizes,
            massConcentrations=mass_concentrations,
            numberConcentrations=number_concentrations,
            typicalParticleSize=typical_particle_size,
            location=self.device_configuration.location,
        )

        await self.topics.evt_sensorStatus.set_write(
            sensorName=self.device_configuration.name,
            sensorStatus=sensor_status,
            serverStatus=response_code,
        )
