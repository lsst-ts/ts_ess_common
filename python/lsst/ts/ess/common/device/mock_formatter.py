# This file is part of ts_ess_common.
#
# Developed for the Vera C. Rubin Observatory Telescope and Site Systems.
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

__all__ = [
    "MockAzimuthConfig",
    "MockDewPointConfig",
    "MockDirectionConfig",
    "MockDistanceConfig",
    "MockElectricFieldStrengthConfig",
    "MockFormatter",
    "MockHumidityConfig",
    "MockPressureConfig",
    "MockStrikeRateConfig",
    "MockTemperatureConfig",
    "MockWindSpeedConfig",
]

import types
from abc import ABC, abstractmethod

# The minimum and maximum azimuth values [deg].
MockAzimuthConfig = types.SimpleNamespace(min=0.0, max=360.0)

# The minimum and maximum dew point values [ºC].
MockDewPointConfig = types.SimpleNamespace(min=18.0, max=30.0)

# The minimum and maximum direction values [deg].
MockDirectionConfig = types.SimpleNamespace(min=0, max=360)

# The minimum and maximum distance values [km].
MockDistanceConfig = types.SimpleNamespace(min=0, max=300)

# The minimum and maximum electric field strength values [kV/m].
MockElectricFieldStrengthConfig = types.SimpleNamespace(min=-20.0, max=20.0)

# The minimum and maximum humidity values [%].
MockHumidityConfig = types.SimpleNamespace(min=5.0, max=95.0)

# The minimum and maximum air pressure values [mbar].
MockPressureConfig = types.SimpleNamespace(min=10.0, max=1100.0)

# The minimum and maximum strike rates (strikes/min).
MockStrikeRateConfig = types.SimpleNamespace(min=0, max=999)

# The minimum and maximum temperatures [ºC].
MockTemperatureConfig = types.SimpleNamespace(min=18.0, max=30.0)

# The minimum and maximum wind speed values [m/s].
MockWindSpeedConfig = types.SimpleNamespace(min=0.0, max=10.0)


class MockFormatter(ABC):
    @abstractmethod
    def format_output(
        self,
        num_channels: int = 0,
        disconnected_channel: int = 0,
        missed_channels: int = 0,
    ) -> list[str]:
        """Create a formatted output of a sensor.

        Parameters
        ----------
        num_channels : `int`
            The number of channels of the sensor, or 0 if this doesn't
            apply to the specific sensor type.
        disconnected_channel : `int`
            The disconnected channel, or -1 if the test case doesn't
            involve a disconnected channel.
        missed_channels : `int`
            The missed channels, or 0 if the test case doesn't
            involve missed channels.

        Returns
        -------
        `list`
            The list of strings representing the formatted output of a
            sensor.
        """
        raise NotImplementedError
