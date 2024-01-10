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

import unittest

from lsst.ts.ess import common
from lsst.ts.ess.common.test_utils import MockTestTools


class MockDeviceTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_mock_hx85a_device(self) -> None:
        """Test the MockDevice with a nominal configuration, i.e. no
        disconnected channels and no truncated data.
        """
        mtt = MockTestTools()
        await mtt.check_mock_device(sensor_type=common.SensorType.HX85A)

    async def test_mock_hx85a_device_with_truncated_output(self) -> None:
        """Test the MockDevice with no disconnected channels and truncated data
        for two channels.
        """
        mtt = MockTestTools()
        await mtt.check_mock_device(
            sensor_type=common.SensorType.HX85A, missed_channels=2
        )

    async def test_mock_hx85a_device_in_error_state(self) -> None:
        """Test the MockDevice in error state meaning it will only return empty
        strings.
        """
        mtt = MockTestTools()
        await mtt.check_mock_device(
            sensor_type=common.SensorType.HX85A, in_error_state=True
        )
