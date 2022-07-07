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

__all__ = ["MockTestTools", "SensorReply"]

import math
from typing import TypedDict

try:
    import pytest
except ImportError:
    raise ImportError(
        "Failed to import pytest. test_utils is only available for testing purposes. To use it "
        "install pytest manually with 'conda install pytest' or install the full build suite with "
        "'conda install -c lsstts ts-conda-build'"
    )

from lsst.ts.ess import common


class SensorReply(TypedDict):
    """`TypedDict` for MyPy checking of sensor replies."""

    name: str
    timestamp: float
    response_code: str
    sensor_telemetry: list


class MockTestTools:
    def check_hx85a_reply(
        self,
        reply: SensorReply,
        name: str,
        missed_channels: int = 0,
        in_error_state: bool = False,
    ) -> None:
        device_name = reply["name"]
        time = float(reply["timestamp"])
        response_code = reply["response_code"]
        resp: list[float] = []
        for value in reply["sensor_telemetry"]:
            assert isinstance(value, float)
            resp.append(value)

        assert name == device_name
        assert time > 0
        if in_error_state:
            assert common.ResponseCode.DEVICE_READ_ERROR == response_code
        else:
            assert common.ResponseCode.OK == response_code
        assert len(resp) == 3
        for i in range(0, 3):
            if i < missed_channels or in_error_state:
                assert math.isnan(resp[i])
            else:
                if i == 0:
                    assert common.device.MockHumidityConfig.min <= resp[i]
                    assert resp[i] <= common.device.MockHumidityConfig.max
                elif i == 1:
                    assert common.device.MockTemperatureConfig.min <= resp[i]
                    assert resp[i] <= common.device.MockTemperatureConfig.max
                else:
                    assert common.device.MockDewPointConfig.min <= resp[i]
                    assert resp[i] <= common.device.MockDewPointConfig.max

    def check_hx85ba_reply(
        self,
        reply: SensorReply,
        name: str,
        missed_channels: int = 0,
        in_error_state: bool = False,
    ) -> None:
        device_name = reply["name"]
        time = float(reply["timestamp"])
        response_code = reply["response_code"]
        resp: list[float] = []
        for value in reply["sensor_telemetry"]:
            assert isinstance(value, float)
            resp.append(value)

        assert name == device_name
        assert time > 0
        if in_error_state:
            assert common.ResponseCode.DEVICE_READ_ERROR == response_code
        else:
            assert common.ResponseCode.OK == response_code
        assert len(resp) == 4

        # Skip the fourth value since it is derived from the first two and it
        # gets validated below.
        for i in range(0, 3):
            if i < missed_channels or in_error_state:
                assert math.isnan(resp[i])
            else:
                if i == 0:
                    assert common.device.MockHumidityConfig.min <= resp[i]
                    assert resp[i] <= common.device.MockHumidityConfig.max
                elif i == 1:
                    assert common.device.MockTemperatureConfig.min <= resp[i]
                    assert resp[i] <= common.device.MockTemperatureConfig.max
                else:
                    assert common.device.MockPressureConfig.min <= resp[i]
                    assert resp[i] <= common.device.MockPressureConfig.max

        dew_point = common.sensor.Hx85baSensor.compute_dew_point(
            relative_humidity=resp[0], temperature=resp[1]
        )
        assert resp[3] == pytest.approx(dew_point, nan_ok=True, rel=1e-4)

    def check_temperature_reply(
        self,
        reply: SensorReply,
        name: str,
        num_channels: int = 0,
        disconnected_channel: int = -1,
        missed_channels: int = 0,
        in_error_state: bool = False,
    ) -> None:
        device_name = reply["name"]
        time = float(reply["timestamp"])
        response_code = reply["response_code"]
        resp: list[float] = []
        for value in reply["sensor_telemetry"]:
            assert isinstance(value, float)
            resp.append(value)

        assert name == device_name
        assert time > 0
        if in_error_state:
            assert common.ResponseCode.DEVICE_READ_ERROR == response_code
        else:
            assert common.ResponseCode.OK == response_code
        assert len(resp) == num_channels
        for i in range(0, num_channels):
            if i < missed_channels or in_error_state:
                assert math.isnan(resp[i])
            elif i == disconnected_channel:
                assert math.isnan(resp[i])
            else:
                assert common.device.MockTemperatureConfig.min <= resp[i]
                assert resp[i] <= common.device.MockTemperatureConfig.max
