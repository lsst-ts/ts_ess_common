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

__all__ = ["add_missing_telemetry"]

import math
import typing


def add_missing_telemetry(
    telemetry: typing.List[float], expected_length: int
) -> typing.List[float]:
    """Prepend a telemetry list with NaN values to make sure that it has the
    expected length.

    Parameters
    ----------
    telemetry : `list`
        The list of telemetry values to prepend to.
    expected_length : `int`
        The expected length of the telemetry list.

    Returns
    -------
    `list`
        The telemetry list or, if the length of the telemetry list is shorter
        then the expected length, the telemetry list with NaN values prepended
        such that the legth matches the expected length.
    """
    if len(telemetry) < expected_length:
        num_missing = expected_length - len(telemetry)
        return [math.nan] * num_missing + telemetry
    else:
        return telemetry
