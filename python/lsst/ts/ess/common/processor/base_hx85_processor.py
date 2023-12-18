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

__all__ = ["BaseHx85Processor"]

import abc

import numpy as np

from .base_processor import BaseProcessor


class BaseHx85Processor(BaseProcessor, abc.ABC):
    async def write_humidity_etc(
        self,
        timestamp: float,
        dew_point: float | None,
        pressure: float | None,
        relative_humidity: float | None,
        temperature: float | None,
        isok: bool,
    ) -> None:
        """Write relative humidity and related quantities.

        Parameters
        ----------
        timestamp : `float` | `None`
            Time at which the data was measured (TAI, unix seconds)
        dew_point : `float` | `None`
            Dew point (C)
        pressure : `float` | `None`
            Parometric pressure (Pa)
        relative_humidity : `float` | `None`
            Relative humidity (%)
        temperature : `float` | `None`
            Air temperature (C)
        isok : `bool`
            Is the data valid?
        """
        if dew_point is not None:
            await self.topics.tel_dewPoint.set_write(
                sensorName=self.device_configuration.name,
                timestamp=timestamp,
                dewPointItem=dew_point if isok else np.nan,
                location=self.device_configuration.location,
            )
        if pressure is not None:
            nelts = len(self.topics.tel_pressure.DataType().pressureItem)
            pressure_array = [np.nan] * nelts
            if isok:
                pressure_array[0] = pressure
            await self.topics.tel_pressure.set_write(
                sensorName=self.device_configuration.name,
                timestamp=timestamp,
                pressureItem=pressure_array,
                numChannels=1,
                location=self.device_configuration.location,
            )
        if relative_humidity is not None:
            await self.topics.tel_relativeHumidity.set_write(
                sensorName=self.device_configuration.name,
                timestamp=timestamp,
                relativeHumidityItem=relative_humidity if isok else np.nan,
                location=self.device_configuration.location,
            )
        if temperature is not None:
            nelts = len(self.topics.tel_temperature.DataType().temperatureItem)
            temperature_array = [np.nan] * nelts
            if isok:
                temperature_array[0] = temperature
            await self.topics.tel_temperature.set_write(
                sensorName=self.device_configuration.name,
                timestamp=timestamp,
                temperatureItem=temperature_array,
                numChannels=1,
                location=self.device_configuration.location,
            )
