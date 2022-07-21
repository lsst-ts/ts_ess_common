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

__all__ = ["MockTemperatureFormatter"]

import random

from ..constants import DISCONNECTED_VALUE
from .mock_formatter import MockFormatter, MockTemperatureConfig


def format_temperature(i: int, disconnected_channel: int, missed_channels: int) -> str:
    """Creates a formatted string representing a temperature for the given
    channel.

    Parameters
    ----------
    i : `int`
        The 0-based temperature channel.
    disconnected_channel : `int`
        The index of the disconnected channel.
    missed_channels : `int`
        The number of missed channels.
    Returns
    -------
    s : `str`
        A string representing a temperature.
    """
    if i < missed_channels:
        return ""

    prefix = f"C{i:02d}="
    value = random.uniform(MockTemperatureConfig.min, MockTemperatureConfig.max)
    if i == disconnected_channel:
        value = float(DISCONNECTED_VALUE)
    return f"{prefix}{value:09.4f}"


class MockTemperatureFormatter(MockFormatter):
    def format_output(
        self,
        num_channels: int = 0,
        disconnected_channel: int = -1,
        missed_channels: int = 0,
    ) -> list[str]:
        output = [
            format_temperature(i, disconnected_channel, missed_channels)
            for i in range(0, num_channels)
        ]
        return output
