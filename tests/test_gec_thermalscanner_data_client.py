# This file is part of ts_ess_csc.
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
import math
import types
import unittest
from unittest.mock import AsyncMock, MagicMock

from lsst.ts.ess import common


class GecThermalscannerDataClientTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_gec_thermalscanner_data_client(self) -> None:
        log = logging.getLogger()

        tel_temperature = types.SimpleNamespace(
            data=types.SimpleNamespace(temperatureItem=[math.nan, math.nan, math.nan, math.nan])
        )
        tel_temperature.DataType = MagicMock(
            return_value=types.SimpleNamespace(temperatureItem=[math.nan, math.nan, math.nan, math.nan])
        )
        tel_temperature.set = MagicMock()
        tel_temperature.set_write = AsyncMock()
        topics = types.SimpleNamespace(tel_temperature=tel_temperature)

        config_dict = dict(
            host="localhost",
            port=5000,
            connect_timeout=5,
            read_timeout=1,
            max_read_timeouts=5,
            location="Test Location",
            sensor_name="Test GEC",
        )
        self.config = types.SimpleNamespace(**config_dict)

        data_client = common.data_client.GecThermalscannerDataClient(
            config=self.config,
            topics=topics,
            log=log,
            simulation_mode=1,
        )

        await data_client.start()
        await asyncio.sleep(1.0)
        for write_topic in data_client.write_topics:
            write_topic.set_write.assert_called()
        await data_client.stop()
