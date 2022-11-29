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
    "MockEFM100CFormatter",
    "MockLD250NoiseFormatter",
    "MockLD250StatusFormatter",
    "MockLD250StrikeFormatter",
]

import random

from ..constants import LD250TelemetryPrefix
from .mock_formatter import (
    MockAzimuthConfig,
    MockDistanceConfig,
    MockElectricFieldStrengthConfig,
    MockFormatter,
    MockStrikeRateConfig,
)


def random_checksum() -> str:
    """Return a 2 digit random hex string that serves as a checksum."""
    return f"{random.randint(0, 255):02X}"


class MockEFM100CFormatter(MockFormatter):
    def __init__(self) -> None:
        self.in_error_state = False

    def format_output(
        self,
        num_channels: int = 0,
        disconnected_channel: int = 0,
        missed_channels: int = 0,
    ) -> list[str]:
        efs = random.uniform(
            MockElectricFieldStrengthConfig.min, MockElectricFieldStrengthConfig.max
        )
        fault = int(self.in_error_state)
        return [f"${efs:+06.2f}", f"{fault}*{random_checksum()}"]


class MockLD250NoiseFormatter(MockFormatter):
    def format_output(
        self,
        num_channels: int = 0,
        disconnected_channel: int = 0,
        missed_channels: int = 0,
    ) -> list[str]:
        return [f"${LD250TelemetryPrefix.NOISE_PREFIX}*{random_checksum()}"]


class MockLD250StatusFormatter(MockFormatter):
    def format_output(
        self,
        num_channels: int = 0,
        disconnected_channel: int = 0,
        missed_channels: int = 0,
    ) -> list[str]:
        close_strike_rate = random.randint(
            MockStrikeRateConfig.min, MockStrikeRateConfig.max
        )
        severe_strike_rate = random.randint(
            MockStrikeRateConfig.min, MockStrikeRateConfig.max
        )
        close_alarm_status = random.randint(0, 1)
        severe_alarm_status = random.randint(0, 1)
        gps_heading = random.uniform(MockAzimuthConfig.min, MockAzimuthConfig.max)
        return [
            f"${LD250TelemetryPrefix.STATUS_PREFIX}",
            f"{close_strike_rate:03d}",
            f"{severe_strike_rate:03d}",
            f"{close_alarm_status:1d}",
            f"{severe_alarm_status:1d}",
            f"{gps_heading:05.1f}*{random_checksum()}",
        ]


class MockLD250StrikeFormatter(MockFormatter):
    def format_output(
        self,
        num_channels: int = 0,
        disconnected_channel: int = 0,
        missed_channels: int = 0,
    ) -> list[str]:
        corrested_strike_distance = random.randint(
            MockDistanceConfig.min, MockDistanceConfig.max
        )
        uncorrested_strike_distance = random.randint(
            MockDistanceConfig.min, MockDistanceConfig.max
        )
        bearing = random.uniform(MockAzimuthConfig.min, MockAzimuthConfig.max)
        return [
            f"${LD250TelemetryPrefix.STRIKE_PREFIX}",
            f"{corrested_strike_distance:03d}",
            f"{uncorrested_strike_distance:03d}",
            f"{bearing:05.1f}*{random_checksum()}",
        ]
