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

__all__ = ["MockCsat3bFormatter"]

import random

from ..sensor import compute_signature
from .mock_formatter import MockFormatter, MockTemperatureConfig, MockWindSpeedConfig

# The diagnostic word is a value in the range [0, 63].
_COUNT_RANGE = 64


def format_csat3b_temperature(index: int, missed_channels: int) -> str:
    if index < missed_channels:
        return ""
    else:
        value = random.uniform(MockTemperatureConfig.min, MockTemperatureConfig.max)
        return f"{value:6.5f}"


def format_csat3b_wind_speed(index: int, missed_channels: int) -> str:
    if index < missed_channels:
        return ""
    else:
        value = random.uniform(MockWindSpeedConfig.min, MockWindSpeedConfig.max)
        return f"{value:6.5f}"


class MockCsat3bFormatter(MockFormatter):
    def __init__(self) -> None:
        super().__init__()
        # Record counter with values from 0 to 63.
        self.count = 0

    def format_output(
        self,
        num_channels: int = 0,
        disconnected_channel: int = 0,
        missed_channels: int = 0,
    ) -> list[str]:
        x = format_csat3b_wind_speed(index=0, missed_channels=missed_channels)
        y = format_csat3b_wind_speed(index=1, missed_channels=missed_channels)
        z = format_csat3b_wind_speed(index=2, missed_channels=missed_channels)
        t = format_csat3b_temperature(index=3, missed_channels=missed_channels)
        # Diagnostic word which is 0 unless there is a problem. We assume here
        # that there never is one. This may change in the future.
        d = 0
        self.count = (self.count + 1) % _COUNT_RANGE
        telemetry_values = [x, y, z, t, f"{d}", f"{self.count}"]
        input_str = ",".join(telemetry_values)
        s = compute_signature(input_str, ",")
        telemetry_values.append(hex(s))
        return telemetry_values
