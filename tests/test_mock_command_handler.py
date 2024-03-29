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

import asyncio
import logging
import unittest
from typing import Any

from lsst.ts.ess import common
from lsst.ts.ess.common.test_utils import MockTestTools

TIMEOUT = 5
"""Standard timeout in seconds."""


class MockCommandHandlerTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.log = logging.getLogger(type(self).__name__)
        self.responses: list[dict[common.ResponseCode, Any]] = []
        self.command_handler = common.MockCommandHandler(
            callback=self.callback, simulation_mode=1
        )
        self.device_config_01 = common.DeviceConfig(
            name="Test01",
            num_channels=4,
            dev_type=common.DeviceType.FTDI,
            dev_id="ABC",
            sens_type=common.SensorType.TEMPERATURE,
            baud_rate=19200,
            location="Test1",
        )
        self.device_config_02 = common.DeviceConfig(
            name="Test02",
            dev_type=common.DeviceType.FTDI,
            dev_id="ABC",
            sens_type=common.SensorType.HX85A,
            baud_rate=19200,
            location="Test2",
        )
        self.device_config_03 = common.DeviceConfig(
            name="Test03",
            dev_type=common.DeviceType.FTDI,
            dev_id="ABC",
            sens_type=common.SensorType.HX85BA,
            baud_rate=19200,
            location="Test3",
        )
        self.device_config_04 = common.DeviceConfig(
            name="Test04",
            dev_type=common.DeviceType.FTDI,
            dev_id="ABC",
            sens_type=common.SensorType.CSAT3B,
            baud_rate=115200,
            location="Test4",
        )
        self.configuration = {
            common.Key.DEVICES: [
                self.device_config_01.as_dict(),
                self.device_config_02.as_dict(),
                self.device_config_03.as_dict(),
                self.device_config_04.as_dict(),
            ]
        }
        self.device_configs = {
            self.device_config_01.name: self.device_config_01,
            self.device_config_02.name: self.device_config_02,
            self.device_config_03.name: self.device_config_03,
            self.device_config_04.name: self.device_config_04,
        }

    async def callback(self, response: dict[common.ResponseCode, Any]) -> None:
        self.responses.append(response)

    def validate_response(self, response_code: common.ResponseCode) -> None:
        response = self.responses.pop()
        assert response[common.Key.RESPONSE] == response_code

    async def test_create_device(self) -> None:
        device: common.device.BaseDevice = self.command_handler.create_device(
            device_configuration=self.device_config_01.as_dict()
        )
        assert isinstance(device, common.device.MockDevice)
        assert isinstance(device.sensor, common.sensor.TemperatureSensor)

        device = self.command_handler.create_device(
            device_configuration=self.device_config_02.as_dict()
        )
        assert isinstance(device, common.device.MockDevice)
        assert isinstance(device.sensor, common.sensor.Hx85aSensor)

        device = self.command_handler.create_device(
            device_configuration=self.device_config_03.as_dict()
        )
        assert isinstance(device, common.device.MockDevice)
        assert isinstance(device.sensor, common.sensor.Hx85baSensor)

        device = self.command_handler.create_device(
            device_configuration=self.device_config_04.as_dict()
        )
        assert isinstance(device, common.device.MockDevice)
        assert isinstance(device.sensor, common.sensor.Csat3bSensor)

    async def test_configure(self) -> None:
        await self.command_handler.configure(configuration=self.configuration)
        assert self.configuration == self.command_handler.configuration
        # Make sure that all background threads of mock devices are stopped.
        await self.command_handler.stop_sending_telemetry()

    async def test_start_and_stop_sending_telemetry(self) -> None:
        assert len(self.command_handler.devices) == 0
        with self.assertLogs("MockCommandHandler", level="DEBUG") as log:
            await self.command_handler.stop_sending_telemetry()
        assert "DEBUG:MockCommandHandler:stop_sending_telemetry" in log.output
        assert (
            "WARNING:MockCommandHandler:Not started yet. Ignoring stop command."
            in log.output
        )
        assert len(self.command_handler.devices) == 0

        # The working of the functions is tested in test_handle_command.
        await self.command_handler.configure(configuration=self.configuration)
        assert len(self.command_handler.devices) == 4
        await self.command_handler.stop_sending_telemetry()
        assert len(self.command_handler.devices) == 0

    async def test_handle_command(self) -> None:
        mtt = MockTestTools()
        await self.command_handler.handle_command(
            command=common.Command.CONFIGURE, configuration=self.configuration
        )
        self.validate_response(common.ResponseCode.OK)
        assert self.configuration == self.command_handler.configuration
        assert self.command_handler._started

        # Give some time to the mock sensor to produce data
        while len(self.responses) < len(self.device_configs):
            await asyncio.sleep(0.5)

        devices_names_checked: set[str] = set()
        while len(devices_names_checked) != len(self.device_configs):
            reply = self.responses.pop()
            name = reply[common.Key.TELEMETRY][common.Key.NAME]
            devices_names_checked.add(name)
            device_config = self.device_configs[name]
            reply_to_check = reply[common.Key.TELEMETRY]
            if device_config.sens_type == common.SensorType.TEMPERATURE:
                num_channels = device_config.num_channels
                mtt.check_temperature_reply(
                    reply=reply_to_check, name=name, num_channels=num_channels
                )
            elif device_config.sens_type == common.SensorType.HX85A:
                mtt.check_hx85a_reply(reply=reply_to_check, name=name)
            elif device_config.sens_type == common.SensorType.HX85BA:
                mtt.check_hx85ba_reply(reply=reply_to_check, name=name)
            elif device_config.sens_type == common.SensorType.CSAT3B:
                mtt.check_csat3b_reply(reply=reply_to_check, name=name)
            else:
                raise ValueError(
                    f"Unsupported sensor type {device_config.sens_type} encountered."
                )

        await self.command_handler.stop_sending_telemetry()
        # Give time to the telemetry_task to get cancelled.
        await asyncio.sleep(0.5)
        assert not self.command_handler._started
