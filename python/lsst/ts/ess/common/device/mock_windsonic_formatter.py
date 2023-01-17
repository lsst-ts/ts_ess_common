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

__all__ = ["MockWindsonicFormatter"]

import random

from ..sensor.gill_windsonic import (
    END_CHARACTER,
    GOOD_STATUS,
    START_CHARACTER,
    UNIT_IDENTIFIER,
    WINDSPEED_UNIT,
    compute_checksum,
)
from .mock_formatter import MockDirectionConfig, MockFormatter, MockWindSpeedConfig


class MockWindsonicFormatter(MockFormatter):
    def __init__(self) -> None:
        self.in_error_state = False

    def format_output(
        self,
        num_channels: int = 0,
        disconnected_channel: int = 0,
        missed_channels: int = 0,
    ) -> list[str]:
        direction = (
            f"{random.randint(MockDirectionConfig.min, MockDirectionConfig.max):03d}"
        )
        speed = (
            f"{random.uniform(MockWindSpeedConfig.min, MockWindSpeedConfig.max):06.2f}"
        )
        checksum_string = (
            f"{UNIT_IDENTIFIER},{direction},{speed},{WINDSPEED_UNIT},{GOOD_STATUS},"
        )
        checksum = f"{compute_checksum(checksum_string):02x}"
        return [
            f"{START_CHARACTER}{UNIT_IDENTIFIER}",
            direction,
            speed,
            WINDSPEED_UNIT,
            GOOD_STATUS,
            f"{END_CHARACTER}{checksum}",
        ]
