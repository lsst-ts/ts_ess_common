# This file is part of ts_ess_dataclients.
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

import jsonschema
from lsst.ts.ess import dataclients

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)


class ConfigSchemaTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_config_schema(self) -> None:
        device_config_01 = dataclients.DeviceConfig(
            name="Test01",
            num_channels=4,
            dev_type=dataclients.DeviceType.FTDI.value,
            dev_id="ABC",
            sens_type=dataclients.SensorType.TEMPERATURE.value,
            baud_rate=19200,
            location="bla,bla,bla,bla",
        )
        device_config_02 = dataclients.DeviceConfig(
            name="Test02",
            dev_type=dataclients.DeviceType.SERIAL.value,
            dev_id="ABC",
            sens_type=dataclients.SensorType.WINDSONIC.value,
            baud_rate=19200,
            location="Motor 1 temp,Motor 2 temp,Strut 7 temp,Strut 8 temp,Strut 9 "
            "temp,Strut 10 temp,Strut 11 temp,Strut 12 temp",
        )
        configuration = {
            dataclients.Key.DEVICES: [
                device_config_01.as_dict(),
                device_config_02.as_dict(),
            ]
        }

        # Validate the configurations against the JSON schema.
        jsonschema.validate(configuration, dataclients.CONFIG_SCHEMA)
