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
import types
import typing
import unittest

from lsst.ts.ess import common

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)


class ReadLoopDataClientTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.log = logging.getLogger()
        self.topics = types.SimpleNamespace()
        self.config = types.SimpleNamespace(name="test_config", max_read_timeouts=5)
        self.data_client = common.TestReadLoopDataClient(
            config=self.config, topics=self.topics, log=self.log
        )

    async def validate_data_client(
        self, task: typing.Callable, expect_error: bool
    ) -> None:
        if expect_error:
            self.data_client.do_timeout = True
        assert self.data_client.num_read_data == 0
        self.data_client.data_read_event.clear()
        await self.data_client.connect()
        running_task = asyncio.create_task(task())
        if not expect_error:
            await self.data_client.data_read_event.wait()
        else:
            with self.assertRaises(asyncio.TimeoutError):
                await running_task
        assert self.data_client.num_read_data == (0 if expect_error else 1)

    async def test_nominal_read_data(self) -> None:
        await self.validate_data_client(self.data_client.read_data, expect_error=False)

    async def test_error_read_data(self) -> None:
        await self.validate_data_client(self.data_client.read_data, expect_error=True)

    async def test_nominal_run_loop(self) -> None:
        await self.validate_data_client(
            task=self.data_client.read_loop, expect_error=False
        )

    async def test_error_run_loop(self) -> None:
        await self.validate_data_client(
            task=self.data_client.read_loop, expect_error=True
        )

    async def test_nominal_run(self) -> None:
        await self.validate_data_client(task=self.data_client.run, expect_error=False)

    async def test_error_run(self) -> None:
        await self.validate_data_client(task=self.data_client.run, expect_error=True)
