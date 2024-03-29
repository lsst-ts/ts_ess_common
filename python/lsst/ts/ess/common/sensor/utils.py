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

__all__ = ["add_missing_telemetry", "compute_dew_point_magnus"]

import math

from ..constants import TelemetryDataType


def add_missing_telemetry(
    telemetry: TelemetryDataType, expected_length: int
) -> TelemetryDataType:
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
        such that the length matches the expected length.
    """
    if len(telemetry) < expected_length:
        num_missing = expected_length - len(telemetry)
        # This next line is necessary to keep mypy happy.
        nan_list: TelemetryDataType = [math.nan] * num_missing
        return nan_list + telemetry
    else:
        return telemetry


def compute_dew_point_magnus(relative_humidity: float, temperature: float) -> float:
    """Compute dew point using the Magnus formula.

    Parameters
    ----------
    relative_humidity : `float`
        Relative humidity (%)
    temperature : `float`
        Air temperature (C)

    Returns
    -------
    `float`
        Dew point (C)
    """
    β = 17.62
    λ = 243.12
    f = math.log(relative_humidity * 0.01) + β * temperature / (λ + temperature)
    return λ * f / (β - f)
