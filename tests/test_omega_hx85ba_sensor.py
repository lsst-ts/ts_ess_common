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

import logging
import unittest

import numpy as np
import pytest
from lsst.ts.ess import common

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)


class OmegaHx85baSensorTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_dew_point(self) -> None:
        # Test data from
        # doc/Dewpoint_Calculation_Humidity_Sensor_E.pdf
        # RH=10%, T=25°C -> Dew point = -8.77°C
        # RH=90%, T=50°C -> Dew point = 47.90°C
        # List of (data dict for the hx85a topic, expected dew point)
        data_list = [
            (dict(relativeHumidity=10.0, temperature=25.0), -8.77),
            (dict(relativeHumidity=90.0, temperature=50.0), 47.90),
        ]
        # Test the compute_dew_point static method
        for data_dict, desired_dew_point in data_list:
            dew_point = common.sensor.Hx85baSensor.compute_dew_point(
                relative_humidity=data_dict["relativeHumidity"],
                temperature=data_dict["temperature"],
            )
            assert dew_point == pytest.approx(desired_dew_point, abs=0.005)

    async def test_extract_telemetry(self) -> None:
        log = logging.getLogger(type(self).__name__)
        sensor = common.sensor.Hx85baSensor(log)
        line = f"%RH=38.86,AT°C=24.32,Pmb=911.40{sensor.terminator}"
        reply = await sensor.extract_telemetry(line=line)
        assert reply == pytest.approx([38.86, 24.32, 911.40, 9.42], abs=0.005)
        line = f"86,AT°C=24.32,Pmb=911.40{sensor.terminator}"
        reply = await sensor.extract_telemetry(line=line)
        assert reply == pytest.approx(
            [np.nan, 24.32, 911.40, np.nan], abs=0.005, nan_ok=True
        )
        with pytest.raises(ValueError):
            line = f"%RH=38.86,AT°C==24.32,Pmb=911.40{sensor.terminator}"
            reply = await sensor.extract_telemetry(line=line)
        line = f"{sensor.terminator}"
        reply = await sensor.extract_telemetry(line=line)
        assert reply == pytest.approx([np.nan, np.nan, np.nan, np.nan], nan_ok=True)
