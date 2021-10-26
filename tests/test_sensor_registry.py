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

from lsst.ts.ess import common

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)

TIMEOUT = 5
"""Standard timeout in seconds."""


class SensorRegistryTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.log = logging.getLogger(type(self).__name__)
        self.device_config_01 = common.DeviceConfig(
            name="Test01",
            num_channels=4,
            dev_type=common.DeviceType.FTDI,
            dev_id="ABC",
            sens_type=common.SensorType.TEMPERATURE,
        )
        self.device_config_02 = common.DeviceConfig(
            name="Test02",
            dev_type=common.DeviceType.FTDI,
            dev_id="ABC",
            sens_type=common.SensorType.HX85A,
        )
        self.device_config_03 = common.DeviceConfig(
            name="Test03",
            dev_type=common.DeviceType.FTDI,
            dev_id="ABC",
            sens_type=common.SensorType.HX85BA,
        )

    async def test_create_sensor(self) -> None:
        sensor: common.sensor.BaseSensor = common.sensor.create_sensor(
            device_configuration=self.device_config_01.as_dict(), log=self.log
        )
        assert isinstance(sensor, common.sensor.TemperatureSensor)

        sensor = common.sensor.create_sensor(
            device_configuration=self.device_config_02.as_dict(), log=self.log
        )
        assert isinstance(sensor, common.sensor.Hx85aSensor)

        sensor = common.sensor.create_sensor(
            device_configuration=self.device_config_03.as_dict(), log=self.log
        )
        assert isinstance(sensor, common.sensor.Hx85baSensor)
