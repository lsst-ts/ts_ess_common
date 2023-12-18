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

__all__ = ["Hx85baProcessor"]

from collections.abc import Sequence

from .base_hx85_processor import BaseHx85Processor
from .utils import mbar_to_pa


class Hx85baProcessor(BaseHx85Processor):
    async def process_telemetry(
        self,
        timestamp: float,
        response_code: int,
        sensor_data: Sequence[float | int | str],
    ) -> None:
        """Process HX85A humidity sensor telemetry.

        Parameters
        ----------
        timestamp : `float`
            The timestamp of the data.
        response_code : `int`
            The ResponseCode
        sensor_data : each of type `float`
            A Sequence of floats representing the sensor telemetry data:

            * relative humidity (%)
            * air temperature (C)
            * dew point (C)
        """
        await self.write_humidity_etc(
            timestamp=timestamp,
            dew_point=float(sensor_data[3]),
            pressure=mbar_to_pa(float(sensor_data[2])),
            relative_humidity=float(sensor_data[0]),
            temperature=float(sensor_data[1]),
            isok=response_code == 0,
        )
        await self.topics.evt_sensorStatus.set_write(
            sensorName=self.device_configuration.name,
            sensorStatus=0,
            serverStatus=response_code,
        )
