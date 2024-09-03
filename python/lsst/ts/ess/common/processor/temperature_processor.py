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

__all__ = ["TemperatureProcessor"]

from collections.abc import Sequence

import numpy as np

from .base_processor import BaseProcessor


class TemperatureProcessor(BaseProcessor):
    async def process_telemetry(
        self,
        timestamp: float,
        response_code: int,
        sensor_data: Sequence[float | str | int],
    ) -> None:
        """Process temperature telemetry.

        Parameters
        ----------
        timestamp : `float`
            The timestamp of the data.
        response_code : `int`
            The ResponseCode
        sensor_data : each of type `float`
            A Sequence of float representing the sensor telemetry data.
        """
        # Array of NaNs used to initialize reported temperatures.
        num_temperatures = len(self.topics.tel_temperature.DataType().temperatureItem)
        temperature = [np.nan] * num_temperatures

        isok = response_code == 0
        if isok:
            temperature[: self.device_configuration.num_channels] = sensor_data  # type: ignore

        # Make sure that all "unused" locations are set to NaN.
        location_items = self.device_configuration.location.split(",")
        location_item: str
        for index, location_item in enumerate(location_items):
            if location_item.strip().lower() == "unused":
                temperature[index] = np.nan

        # Replace any None value with NaN.
        temperature = [np.nan if t is None else t for t in temperature]

        await self.topics.tel_temperature.set_write(
            sensorName=self.device_configuration.name,
            timestamp=timestamp,
            numChannels=self.device_configuration.num_channels,
            temperatureItem=temperature,
            location=self.device_configuration.location,
        )
        await self.topics.evt_sensorStatus.set_write(
            sensorName=self.device_configuration.name,
            sensorStatus=0,
            serverStatus=response_code,
        )
