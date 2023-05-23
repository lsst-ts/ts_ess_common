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
    "add_missing_telemetry",
    "compute_dew_point_magnus",
    "get_circular_mean_and_std_dev",
    "get_median_and_std_dev",
]

import cmath
import math

import numpy as np

from .constants import TelemetryDataType

_QUANTILE = [0.25, 0.5, 0.75]
_STD_DEV_FACTOR = 0.741


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

    Notes
    -----
    The :download:`Magnus formula <../dewpoint_magnus_formula.pdf>` is::

        dp = λ·f / (β - f)

        Where:

        • dp is dew point in deg C
        • β = 17.62
        • λ = 243.12 C
        • f = ln(rh/100) + (β·t)/(λ+t))
        • t = air temperature in deg C
        • rh = relative humidity in %
    """
    β = 17.62
    λ = 243.12
    f = math.log(relative_humidity * 0.01) + β * temperature / (λ + temperature)
    return λ * f / (β - f)


def get_circular_mean_and_std_dev(
    angles: np.ndarray | list[float],
) -> tuple[float, float]:
    """Compute the circular mean and circular standard deviation
    of an array of angles in degrees.

    Parameters
    ----------
    angles : `list` of `float`
        A sequence of angles in degrees.

    Returns
    -------
    mean : `float`
        The circular mean.
    std_dev : `float`
        The circular standard deviation, which ranges from 0 to math.inf.

    Raises
    ------
    ValueError
        If ``angles`` is empty.
    """
    if len(angles) == 0:
        raise ValueError("angles is empty; you must provide at least one value")
    # See https://en.wikipedia.org/wiki/Directional_statistics
    # for information about statistics on direction.
    complex_sum = np.sum(np.exp(1j * np.radians(angles))) / len(angles)
    circular_mean = math.degrees(cmath.phase(complex_sum))
    if circular_mean < 0:
        circular_mean += 360
    try:
        circular_std = math.degrees(math.sqrt(-2 * math.log(abs(complex_sum))))
    except ValueError:
        circular_std = math.inf
    return (circular_mean, circular_std)


def get_median_and_std_dev(
    data: np.ndarray | list[float] | list[list[float]], axis: int | None = None
) -> tuple[np.ndarray, np.ndarray] | tuple[float, float]:
    """Compute the median and estimated standard deviation using quantiles.

    Parameters
    ----------
    data : `list` of `float`
        The data to compute the median for.
    axis : `int`
        The axis of the data to use.

    Returns
    -------
    median : `float`
        The median.
    std_dev : `float`
        Estimate of the standard deviation.
    """
    q25, median, q75 = np.quantile(data, _QUANTILE, axis=axis)
    std_dev = _STD_DEV_FACTOR * (q75 - q25)
    return median, std_dev
