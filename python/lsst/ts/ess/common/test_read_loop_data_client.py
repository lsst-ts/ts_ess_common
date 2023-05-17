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

from __future__ import annotations

__all__ = ["TestReadLoopDataClient"]

import asyncio
import logging
import types
from typing import TYPE_CHECKING, Any

import yaml

from .base_read_loop_data_client import BaseReadLoopDataClient

if TYPE_CHECKING:
    from lsst.ts import salobj


class TestReadLoopDataClient(BaseReadLoopDataClient):
    """Concrete subclass of BaseReadLoopDataClient for unit tests."""

    __test__ = False  # Stop pytest from warning that this is not a test.

    def __init__(
        self,
        config: types.SimpleNamespace,
        topics: salobj.Controller | types.SimpleNamespace,
        log: logging.Logger,
        simulation_mode: int = 0,
    ) -> None:
        super().__init__(
            config=config, topics=topics, log=log, simulation_mode=simulation_mode
        )

        # Keep track of how often the read_data coro is called to mock reading
        # data.
        self.num_read_data = 0

        # Event to monitor for results in unit tests.
        self.data_read_event = asyncio.Event()

        # This is set to a low number so the unit tests won't take much time.
        self.max_read_timouts = 2

        # This is set to a low number so the unit tests won't take much time.
        self.read_sleep_time = 0.2

        # For mocking timeouts, set this to True.
        self.do_timeout = False

    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        """Return a schema.

        The schema is ignored in this unit test, as it is applied
        by the ESS CSC. But providing a schema does present testing
        opportunities in ts_ess_csc.
        """
        return yaml.safe_load(
            """
$schema: http://json-schema.org/draft-07/schema#
description: trival schema for BaseDataClient
type: object
properties:
  name:
    type: string
  max_read_timeouts:
    type: int
    default: 5
required:
  - name
  - max_read_timeouts
additionalProperties: false
"""
        )

    def descr(self) -> str:
        return f"name={self.config.name}"

    async def read_data(self) -> None:
        if self.do_timeout:
            raise asyncio.TimeoutError
        self.num_read_data += 1
        self.data_read_event.set()
        await asyncio.sleep(self.read_sleep_time)
