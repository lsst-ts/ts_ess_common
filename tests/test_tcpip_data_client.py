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
import pathlib
import types
import unittest
from unittest.mock import ANY, AsyncMock, MagicMock

import yaml
from lsst.ts.ess import common

CONFIG_PATH = pathlib.Path(__file__).parent / "data" / "config"


class TcpipDataClientTestCase(unittest.IsolatedAsyncioTestCase):
    def get_config(self, filename: str) -> types.SimpleNamespace:
        """Get a config dict from tests/data.

        This should always be a good config,
        because validation is done by the ESS CSC,
        not the data client.

        Parameters
        ----------
        filename : `str` or `pathlib.Path`
            Name of config file, including ".yaml" suffix.

        Returns
        -------
        config : types.SimpleNamespace
            The config dict.
        """
        with open(CONFIG_PATH / filename, "r") as f:
            config_dict = yaml.safe_load(f.read())
        return types.SimpleNamespace(**config_dict)

    async def test_tcpip_data_client(self) -> None:
        log = logging.getLogger()
        config = self.get_config("tcpip_temperature_sensor.yaml")
        device_configuration = {
            common.Key.NAME.value: config.name,
            common.Key.SENSOR_TYPE.value: config.sensor_type,
            common.Key.CHANNELS.value: config.channels,
        }
        async with common.MockTelemetryServer(
            host=config.host, port=0, log=log, device_configuration=device_configuration
        ) as server:
            config.port = server.port
            evt_sensor_status = AsyncMock()
            tel_temperature = AsyncMock()
            tel_temperature.DataType = MagicMock(
                return_value=types.SimpleNamespace(temperatureItem=[0.0, 0.0, 0.0, 0.0])
            )
            topics = types.SimpleNamespace(
                **{
                    "evt_sensorStatus": evt_sensor_status,
                    "tel_temperature": tel_temperature,
                },
            )
            async with common.data_client.TcpipDataClient(
                config=config, topics=topics, log=log, simulation_mode=1
            ):
                await asyncio.sleep(2)

            evt_sensor_status.set_write.assert_called_with(
                sensorName=config.name, sensorStatus=0, serverStatus=0
            )
            tel_temperature.set_write.assert_called_with(
                sensorName=config.name,
                timestamp=ANY,
                temperatureItem=[ANY] * config.channels,
                numChannels=config.channels,
                location=config.location,
            )
