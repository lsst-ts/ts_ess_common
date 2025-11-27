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
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import yaml
from lsst.ts.ess import common

CONFIG_PATH = pathlib.Path(__file__).parent / "data" / "config"


class ControllerDataClientTestCase(unittest.IsolatedAsyncioTestCase):
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

    async def test_controller_data_client(self) -> None:
        log = logging.getLogger()
        evt_sensor_status = AsyncMock()
        tel_dew_point = AsyncMock()
        tel_relative_humidity = AsyncMock()
        tel_temperature = AsyncMock()
        tel_temperature.DataType = MagicMock(
            return_value=types.SimpleNamespace(temperatureItem=[0.0, 0.0, 0.0, 0.0])
        )
        topics = types.SimpleNamespace(
            **{
                "evt_sensorStatus": evt_sensor_status,
                "tel_dewPoint": tel_dew_point,
                "tel_relativeHumidity": tel_relative_humidity,
                "tel_temperature": tel_temperature,
            }
        )

        config = self.get_config("test_hx85a_sensor.yaml")
        async with common.data_client.ControllerDataClient(
            config=config, topics=topics, log=log, simulation_mode=1
        ):
            await asyncio.sleep(2)

        evt_sensor_status.set_write.assert_called_with(
            sensorName=config.devices[0]["name"], sensorStatus=0, serverStatus=0
        )
        tel_dew_point.set_write.assert_called_with(
            sensorName=config.devices[0]["name"],
            timestamp=ANY,
            dewPointItem=ANY,
            location=config.devices[0]["location"],
        )
        tel_relative_humidity.set_write.assert_called_with(
            sensorName=config.devices[0]["name"],
            timestamp=ANY,
            relativeHumidityItem=ANY,
            location=config.devices[0]["location"],
        )
        tel_temperature.set_write.assert_called_with(
            sensorName=config.devices[0]["name"],
            timestamp=ANY,
            temperatureItem=ANY,
            numChannels=1,
            location=config.devices[0]["location"],
        )

    async def test_controller_data_client_read_error(self) -> None:
        log = logging.getLogger()
        evt_sensor_status = AsyncMock()
        tel_lightningStrikeStatus = AsyncMock()
        evt_lightningStrike = AsyncMock()
        evt_highElectricField = AsyncMock()
        tel_electricFieldStrength = AsyncMock()
        topics = types.SimpleNamespace(
            **{
                "evt_sensorStatus": evt_sensor_status,
                "tel_lightningStrikeStatus": tel_lightningStrikeStatus,
                "evt_lightningStrike": evt_lightningStrike,
                "evt_highElectricField": evt_highElectricField,
                "tel_electricFieldStrength": tel_electricFieldStrength,
            }
        )

        with patch.object(common.sensor.Efm100cSensor, "extract_telemetry") as mock_extract_telemetry:
            mock_extract_telemetry.return_value = []
            config = self.get_config("test_lightning_sensors.yaml")
            async with common.data_client.ControllerDataClient(
                config=config, topics=topics, log=log, simulation_mode=1
            ) as cdc:
                while cdc.num_consecutive_read_timeouts < 2:
                    await asyncio.sleep(1)

                assert cdc.num_consecutive_read_timeouts == 2
