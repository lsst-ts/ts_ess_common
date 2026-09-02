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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

__all__ = ["MockSps30Formatter"]

import datetime
import random

from .mock_formatter import (
    MockFormatter,
    MockParticleConcentrationConfig,
    MockParticleNumberConcentrationConfig,
    MockParticleSizeConfig,
)


class MockSps30Formatter(MockFormatter):
    def format_output(
        self,
        num_channels: int = 0,
        disconnected_channel: int = -1,
        missed_channels: int = 0,
    ) -> list[str]:
        timestamp = datetime.datetime.now(tz=datetime.timezone.utc).timestamp()

        concentrations = [
            random.uniform(MockParticleConcentrationConfig.min, MockParticleConcentrationConfig.max)
            for _ in range(5)
        ]
        num_concentrations = [
            random.uniform(
                MockParticleNumberConcentrationConfig.min, MockParticleNumberConcentrationConfig.max
            )
            for _ in range(5)
        ]
        typical_size = random.uniform(MockParticleSizeConfig.min, MockParticleSizeConfig.max)

        telemetry_data = [
            f"{timestamp:.2f}",
            *[f"{x:.2f}" for x in concentrations],
            *[f"{x:.2f}" for x in num_concentrations],
            f"{typical_size:.2f}",
        ]

        return [",".join(telemetry_data)]
