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

__all__ = ["MockTestTools", "MockDeviceProperties"]

import math
import typing

from lsst.ts.ess import common


class MockDeviceProperties:
    """Container for the properties of a mock device.

    Parameters
    ----------
    name: `str`
        The name of the device.
    num_channels: `int`
        The number of channels.
    missed_channels: `int`
        The number of missed channels.
    disconnected_channel: `int`
        The number of the disconnected channel, or None if all
        channels are connected.
    in_error_state: `bool`
        The mock device is in error state (True) or not (False, the
        default).
    """

    def __init__(
        self,
        name: str,
        num_channels: int = 0,
        missed_channels: int = 0,
        disconnected_channel: int = None,
        in_error_state: bool = False,
    ) -> None:
        self.name: str = name
        self.num_channels = num_channels
        self.missed_channels = missed_channels
        self.disconnected_channel = disconnected_channel
        self.in_error_state = in_error_state


class MockTestTools:
    def check_hx85a_reply(
        self,
        md_props: MockDeviceProperties,
        reply: typing.List[typing.Union[str, float]],
    ) -> None:
        device_name = reply[0]
        time = float(reply[1])
        response_code = reply[2]
        resp: typing.List[typing.SupportsFloat] = []
        for value in reply[3:]:
            assert isinstance(value, float)
            resp.append(value)

        assert md_props.name == device_name
        assert time > 0
        if md_props.in_error_state:
            assert common.ResponseCode.DEVICE_READ_ERROR == response_code
        else:
            assert common.ResponseCode.OK == response_code
        assert len(resp) == 3
        for i in range(0, 3):
            if i < md_props.missed_channels or md_props.in_error_state:
                assert math.isnan(resp[i])
            else:
                if i == 0:
                    assert common.MockHumidityConfig.min <= resp[i]
                    assert resp[i] <= common.MockHumidityConfig.max
                elif i == 1:
                    assert common.MockTemperatureConfig.min <= resp[i]
                    assert resp[i] <= common.MockTemperatureConfig.max
                else:
                    assert common.MockDewPointConfig.min <= resp[i]
                    assert resp[i] <= common.MockDewPointConfig.max

    def check_hx85ba_reply(
        self,
        md_props: MockDeviceProperties,
        reply: typing.List[typing.Union[str, float]],
    ) -> None:
        device_name = reply[0]
        time = float(reply[1])
        response_code = reply[2]
        resp: typing.List[typing.SupportsFloat] = []
        for value in reply[3:]:
            assert isinstance(value, float)
            resp.append(value)

        assert md_props.name == device_name
        assert time > 0
        if md_props.in_error_state:
            assert common.ResponseCode.DEVICE_READ_ERROR == response_code
        else:
            assert common.ResponseCode.OK == response_code
        assert len(resp) == 3
        for i in range(0, 3):
            if i < md_props.missed_channels or md_props.in_error_state:
                assert math.isnan(resp[i])
            else:
                if i == 0:
                    assert common.MockHumidityConfig.min <= resp[i]
                    assert resp[i] <= common.MockHumidityConfig.max
                elif i == 1:
                    assert common.MockTemperatureConfig.min <= resp[i]
                    assert resp[i] <= common.MockTemperatureConfig.max
                else:
                    assert common.MockPressureConfig.min <= resp[i]
                    assert resp[i] <= common.MockPressureConfig.max

    def check_temperature_reply(
        self,
        md_props: MockDeviceProperties,
        reply: typing.List[typing.Union[str, float]],
    ) -> None:
        device_name = reply[0]
        time = float(reply[1])
        response_code = reply[2]
        resp: typing.List[typing.SupportsFloat] = []
        for value in reply[3:]:
            assert isinstance(value, float)
            resp.append(value)

        assert md_props.name == device_name
        assert time > 0
        if md_props.in_error_state:
            assert common.ResponseCode.DEVICE_READ_ERROR == response_code
        else:
            assert common.ResponseCode.OK == response_code
        assert len(resp) == md_props.num_channels
        for i in range(0, md_props.num_channels):
            if i < md_props.missed_channels or md_props.in_error_state:
                assert math.isnan(resp[i])
            elif i == md_props.disconnected_channel:
                assert math.isnan(resp[i])
            else:
                assert common.MockTemperatureConfig.min <= resp[i]
                assert resp[i] <= common.MockTemperatureConfig.max
