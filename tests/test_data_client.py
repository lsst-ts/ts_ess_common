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
import types
import unittest

import pytest
from lsst.ts.ess import common

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)

TIMEOUT = 5
"""Standard timeout in seconds."""


class DataClientTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.log = logging.getLogger()
        self.topics = types.SimpleNamespace()
        self.config = types.SimpleNamespace(name="test_config")

    def test_constructor(self) -> None:
        data_client = common.TestDataClient(
            config=self.config, topics=self.topics, log=self.log
        )
        assert data_client.simulation_mode == 0
        assert isinstance(data_client.log, logging.Logger)

        for simulation_mode in (0, 1):
            data_client = common.TestDataClient(
                config=self.config,
                topics=self.topics,
                log=self.log,
                simulation_mode=simulation_mode,
            )
            assert data_client.simulation_mode == simulation_mode

    async def test_basics(self) -> None:
        data_client = common.TestDataClient(
            config=self.config, topics=self.topics, log=self.log
        )
        assert not data_client.connected
        assert data_client.run_task.done()

        await data_client.start()
        assert data_client.connected
        assert not data_client.run_task.done()

        await data_client.stop()
        assert not data_client.connected
        assert data_client.run_task.done()

    async def test_exceptions(self) -> None:
        data_client = common.TestDataClient(
            config=self.config, topics=self.topics, log=self.log
        )

        data_client.connect_exception = ConnectionError("Test raising")
        data_client.disconnect_exception = ValueError("Test raising")
        data_client.run_exception = RuntimeError("Test raising")
        assert not data_client.connected
        assert data_client.run_task.done()

        with pytest.raises(ValueError):
            await data_client.disconnect()
        with pytest.raises(ConnectionError):
            await data_client.connect()
        with pytest.raises(RuntimeError):
            await data_client.run()
        with pytest.raises(ConnectionError):
            await data_client.start()
        assert not data_client.connected
        assert data_client.run_task.done()

        # disconnect does not set connected False because it raises first.
        data_client.connected = True
        with pytest.raises(ValueError):
            await data_client.disconnect()
        assert data_client.connected
        assert data_client.run_task.done()

        # Stop swallows the exception in disconnect.
        await data_client.stop()
        assert data_client.connected
        assert data_client.run_task.done()

    async def test_registry(self) -> None:
        data_client_class = common.get_data_client_class("TestDataClient")
        assert data_client_class is common.TestDataClient

        # case matters
        with pytest.raises(KeyError):
            common.get_data_client_class("testdataclient")

        # abstract subclasses of BaseDataClass are not registered
        with pytest.raises(KeyError):
            common.get_data_client_class("BaseDataClient")
