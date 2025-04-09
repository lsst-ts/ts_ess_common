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

__all__ = ["sensor_dict", "telemetry_processor_dict"]

import typing

from ..constants import SensorType
from ..processor import (
    AirTurbulenceProcessor,
    AuroraProcessor,
    BaseProcessor,
    Efm100cProcessor,
    Hx85aProcessor,
    Hx85baProcessor,
    Ld250Processor,
    TemperatureProcessor,
    WindsonicProcessor,
)
from ..sensor import (
    BaseSensor,
    Csat3bSensor,
    Efm100cSensor,
    Hx85aSensor,
    Hx85baSensor,
    Ld250Sensor,
    TemperatureSensor,
    WindsonicSensor,
)

# Dict of SensorType: BaseSensor type.
sensor_dict: dict[str, typing.Type[BaseSensor]] = {
    SensorType.CSAT3B: Csat3bSensor,
    SensorType.EFM100C: Efm100cSensor,
    SensorType.HX85A: Hx85aSensor,
    SensorType.HX85BA: Hx85baSensor,
    SensorType.LD250: Ld250Sensor,
    SensorType.TEMPERATURE: TemperatureSensor,
    SensorType.WINDSONIC: WindsonicSensor,
}

# Dict of SensorType: BaseProcessor type.
telemetry_processor_dict: dict[str, typing.Type[BaseProcessor]] = {
    SensorType.CSAT3B: AirTurbulenceProcessor,
    SensorType.EFM100C: Efm100cProcessor,
    SensorType.HX85A: Hx85aProcessor,
    SensorType.HX85BA: Hx85baProcessor,
    SensorType.LD250: Ld250Processor,
    SensorType.TEMPERATURE: TemperatureProcessor,
    SensorType.WINDSONIC: WindsonicProcessor,
    SensorType.AURORA: AuroraProcessor,
}
