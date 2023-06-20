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

import asyncio
import inspect
import logging
import math
from typing import TypedDict

from lsst.ts.ess import common


class SensorReply(TypedDict):
    """`TypedDict` for MyPy checking of sensor replies."""

    name: str
    timestamp: float
    response_code: str
    sensor_telemetry: list


check_reply_func_dict = {
    common.SensorType.CSAT3B: "check_csat3b_reply",
    common.SensorType.EFM100C: "check_efm100c_reply",
    common.SensorType.HX85A: "check_hx85a_reply",
    common.SensorType.HX85BA: "check_hx85ba_reply",
    common.SensorType.LD250: "check_ld250_reply",
    common.SensorType.TEMPERATURE: "check_temperature_reply",
    common.SensorType.WINDSONIC: "check_windsonic_reply",
}

# Maximum number of times to wait before exiting a sleep loop.
MAX_SLEEP_WAITS = 60


class MockTestTools:
    def __init__(self) -> None:
        self.reply: None | dict[str, common.TelemetryDataType] = None

    async def _callback(self, reply: dict[str, common.TelemetryDataType]) -> None:
        self.reply = reply

    async def wait_for_reply(self) -> None:
        self.reply = None
        num_sleep_waits = 0
        while not self.reply:
            await asyncio.sleep(0.1)
            num_sleep_waits = num_sleep_waits + 1
            if num_sleep_waits >= MAX_SLEEP_WAITS:
                raise TimeoutError("Did't get telemetry on time.")

    async def check_mock_device(
        self,
        sensor_type: common.SensorType,
        num_channels: int = 0,
        disconnected_channel: int = -1,
        missed_channels: int = 0,
        in_error_state: bool = False,
        noise: bool = False,
        strike: bool = False,
    ) -> None:
        """Check the working of the MockDevice."""
        log = logging.getLogger(type(self).__name__)
        sensor_class = common.sensor.sensor_registry[sensor_type]
        sensor_arg_values: dict[str, int | logging.Logger] = {"log": log}
        sensor_args = inspect.getfullargspec(sensor_class.__init__)
        if "num_channels" in sensor_args.args:
            sensor_arg_values["num_channels"] = num_channels
        sensor = sensor_class(**sensor_arg_values)
        func = getattr(self, check_reply_func_dict[sensor_type])
        async with common.device.MockDevice(
            name="MockSensor",
            device_id="MockDevice",
            sensor=sensor,
            callback_func=self._callback,
            log=log,
        ) as device:
            device.disconnected_channel = disconnected_channel
            device.missed_channels = missed_channels
            if hasattr(device.mock_formatter, "in_error_state"):
                device.mock_formatter.in_error_state = in_error_state
            else:
                device.in_error_state = in_error_state
            device.noise = noise
            device.strike = strike

            # First read of the telemetry to verify that handling of truncated
            # data is performed correctly if the MockDevice is instructed to
            # produce such data.
            await self.wait_for_reply()
            assert self.reply is not None
            func_arg_values = {
                "reply": self.reply[common.Key.TELEMETRY],
                "name": "MockSensor",
                "in_error_state": in_error_state,
            }
            func_args = inspect.getfullargspec(func)
            if "num_channels" in func_args.args:
                func_arg_values["num_channels"] = num_channels
            if "disconnected_channel" in func_args.args:
                func_arg_values["disconnected_channel"] = disconnected_channel
            if "missed_channels" in func_args.args:
                func_arg_values["missed_channels"] = missed_channels
            func(**func_arg_values)

            # Reset missed_channels for the second read otherwise the
            # check will fail.
            if missed_channels > 0:
                missed_channels = 0

            # Now read the telemetry to verify that no more truncated data
            # is produced if the MockDevice was instructed to produce such
            # data.
            await self.wait_for_reply()
            assert self.reply is not None
            func_arg_values["reply"] = self.reply[common.Key.TELEMETRY]
            if "missed_channels" in func_args.args:
                func_arg_values["missed_channels"] = missed_channels
            func(**func_arg_values)

    def check_csat3b_reply(
        self,
        reply: SensorReply,
        name: str,
        missed_channels: int = 0,
        in_error_state: bool = False,
    ) -> None:
        device_name = reply["name"]
        time = float(reply["timestamp"])
        response_code = reply["response_code"]
        resp: list[float | int] = []
        for value in reply["sensor_telemetry"]:
            assert isinstance(value, float) or isinstance(value, int)
            resp.append(value)

        assert name == device_name
        assert time > 0
        if in_error_state:
            assert common.ResponseCode.DEVICE_READ_ERROR == response_code
        else:
            assert common.ResponseCode.OK == response_code
        # Only check the first 4 items (which are ux, uy, uz and ts) because
        # the rest doesn't matter for the science of Rubin Observatory.
        for i in range(0, 4):
            if i < missed_channels or in_error_state:
                assert math.isnan(resp[i]) if i < 5 else resp[i] == 0
            else:
                if i in [0, 1, 2]:
                    assert common.device.MockWindSpeedConfig.min <= resp[i]
                    assert resp[i] <= common.device.MockWindSpeedConfig.max
                elif i == 3:
                    assert common.device.MockTemperatureConfig.min <= resp[i]
                    assert resp[i] <= common.device.MockTemperatureConfig.max

    def check_ld250_reply(
        self,
        reply: SensorReply,
        name: str,
        in_error_state: bool = False,
    ) -> None:
        device_name = reply["name"]
        time = float(reply["timestamp"])
        response_code = reply["response_code"]
        resp: common.TelemetryDataType = []
        for value in reply["sensor_telemetry"]:
            assert (
                isinstance(value, float)
                or isinstance(value, int)
                or isinstance(value, str)
            )
            resp.append(value)

        assert name == device_name
        assert time > 0
        assert common.ResponseCode.OK == response_code

        if resp[0] == common.LD250TelemetryPrefix.NOISE_PREFIX:
            # Check noise response.
            assert len(resp) == 1
        elif resp[0] == common.LD250TelemetryPrefix.STATUS_PREFIX:
            # Check status response.
            assert len(resp) == 6
            assert common.device.MockStrikeRateConfig.min <= resp[1]
            assert resp[1] <= common.device.MockStrikeRateConfig.max
            assert common.device.MockStrikeRateConfig.min <= resp[2]
            assert resp[2] <= common.device.MockStrikeRateConfig.max
            assert resp[3] in [0, 1]
            assert resp[4] in [0, 1]
            assert common.device.MockAzimuthConfig.min <= resp[5]
            assert resp[5] <= common.device.MockAzimuthConfig.max
        elif resp[0] == common.LD250TelemetryPrefix.STRIKE_PREFIX:
            # Check strike response.
            assert len(resp) == 4
            assert common.device.MockDistanceConfig.min <= resp[1]
            assert resp[1] <= common.device.MockDistanceConfig.max
            assert common.device.MockDistanceConfig.min <= resp[2]
            assert resp[2] <= common.device.MockDistanceConfig.max
            assert common.device.MockAzimuthConfig.min <= resp[3]
            assert resp[3] <= common.device.MockAzimuthConfig.max

    def check_efm100c_reply(
        self,
        reply: SensorReply,
        name: str,
        in_error_state: bool = False,
    ) -> None:
        device_name = reply["name"]
        time = float(reply["timestamp"])
        response_code = reply["response_code"]
        resp: list[float | int] = []
        for value in reply["sensor_telemetry"]:
            assert isinstance(value, float) or isinstance(value, int)
            resp.append(value)

        assert name == device_name
        assert time > 0
        assert common.ResponseCode.OK == response_code

        assert common.device.MockElectricFieldStrengthConfig.min <= resp[0]
        assert resp[0] <= common.device.MockElectricFieldStrengthConfig.max

        if in_error_state:
            assert resp[1] == 1
        else:
            assert resp[1] == 0

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

        if missed_channels > 0 or in_error_state:
            assert math.isnan(resp[3])
        else:
            # Check dew point computed with 2 digits of precision,
            # since that is all the sensor reports.
            dew_point = common.sensor.compute_dew_point_magnus(
                relative_humidity=round(resp[0], ndigits=2),
                temperature=round(resp[1], ndigits=2),
            )
            # The tolerances match pytest.approx.
            assert math.isclose(resp[3], dew_point, rel_tol=1e-6, abs_tol=1e-12)

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

    def check_windsonic_reply(
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
        resp: list[float | int] = []
        assert len(reply["sensor_telemetry"]) == 2
        assert isinstance(reply["sensor_telemetry"][0], float)
        assert isinstance(reply["sensor_telemetry"][1], int)
        for value in reply["sensor_telemetry"]:
            resp.append(value)

        assert name == device_name
        assert time > 0
        if in_error_state:
            assert common.ResponseCode.DEVICE_READ_ERROR == response_code
        else:
            assert common.ResponseCode.OK == response_code
        assert common.device.MockWindSpeedConfig.min <= resp[0]
        assert resp[0] <= common.device.MockWindSpeedConfig.max
        assert common.device.MockDirectionConfig.min <= resp[1]
        assert resp[1] <= common.device.MockDirectionConfig.max
