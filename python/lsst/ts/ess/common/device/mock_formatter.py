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
    "MockFormatter",
    "MockDewPointConfig",
    "MockHumidityConfig",
    "MockPressureConfig",
    "MockTemperatureConfig",
    "MockWindSpeedConfig",
]

from abc import ABC, abstractmethod
import types

# The minimum and maximum temperatures [ºC] used by the mock device.
MockTemperatureConfig = types.SimpleNamespace(min=18.0, max=30.0)

# The minimum and maximum humidity values [%] used by the mock device.
MockHumidityConfig = types.SimpleNamespace(min=5.0, max=95.0)

# The minimum and maximum dew point values [ºC] used by the mock
# device.
MockDewPointConfig = types.SimpleNamespace(min=18.0, max=30.0)

# The minimum and maximum air pressure values [mbar] used by the mock
# device.
MockPressureConfig = types.SimpleNamespace(min=10.0, max=1100.0)

# The minimum and maximum wind speed values [m/s] used by the mock device.
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
