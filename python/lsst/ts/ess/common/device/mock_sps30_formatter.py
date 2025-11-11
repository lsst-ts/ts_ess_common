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

__all__ = ["MockSps30Formatter"]

import random

from lsst.ts.ess.common.device.mock_formatter import MockFormatter
from lsst.ts.ess.common.sensor.sps30_sensor import (
    Sps30Sensor,
    compute_particulate_checksum,
)


class MockSps30Formatter(MockFormatter):
    def format_output(
        self,
        num_channels: int = 0,
        disconnected_channel: int = -1,
        missed_channels: int = 0,
    ) -> list[str]:
        sensor_name = "SPS30"
        timestamp = random.uniform(1609459200, 1609459300)

        sizes = [random.uniform(0, 100) for _ in range(5)]
        concentrations = [random.uniform(0, 1000) for _ in range(5)]
        num_concentrations = [random.uniform(0, 10000) for _ in range(5)]
        typical_size = random.uniform(0.1, 1.0)
        location = "TestLocation"
        status = Sps30Sensor.GOOD_STATUS

        telemetry_data = [
            sensor_name,
            f"{timestamp:.2f}",
            *[f"{x:.2f}" for x in sizes],
            *[f"{x:.2f}" for x in concentrations],
            *[f"{x:.2f}" for x in num_concentrations],
            f"{typical_size:.2f}",
            location,
            status,
        ]

        checksum_string = ",".join(telemetry_data)
        checksum = f"{compute_particulate_checksum(checksum_string):02x}"

        return [f"{Sps30Sensor.START_CHAR}{','.join(telemetry_data)}{Sps30Sensor.END_CHAR}{checksum}"]
