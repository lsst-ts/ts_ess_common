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

__all__ = ["MockHx85baFormatter"]

import typing

from .mock_hx85_formatter import MockHx85Formatter


class MockHx85baFormatter(MockHx85Formatter):
    def format_output(
        self,
        num_channels: int = 0,
        disconnected_channel: int = 0,
        missed_channels: int = 0,
    ) -> typing.List[str]:
        return [
            self._format_hbx85_humidity(index=0, missed_channels=missed_channels),
            self._format_hbx85_temperature(index=1, missed_channels=missed_channels),
            self._format_hbx85_air_pressure(index=2, missed_channels=missed_channels),
        ]
