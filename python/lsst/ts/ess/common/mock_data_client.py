from __future__ import annotations

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

__all__ = ["MockDataClient"]

import asyncio
import logging
import types
from typing import Any, TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from lsst.ts import salobj
from .base_data_client import BaseDataClient


class MockDataClient(BaseDataClient):
    """Trivial concrete subclass of BaseMode."""

    def __init__(
        self,
        config: types.SimpleNamespace,
        topics: salobj.Controller | types.SimpleNamespace,
        log: logging.Logger,
        simulation_mode: int = 0,
    ) -> None:
        self.connected = False
        # Exceptions to raise in the specified methods, or None to not raise.
        # Set to an *instance* of an exception, not a class.
        self.connect_exception: None | Exception = None
        self.disconnect_exception: None | Exception = None
        self.run_exception: None | Exception = None
        self.num_run = 0
        super().__init__(
            config=config, topics=topics, log=log, simulation_mode=simulation_mode
        )

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
required:
  - name
additionalProperties: false
"""
        )

    def descr(self) -> str:
        return f"name={self.config.name}"

    async def connect(self) -> None:
        await asyncio.sleep(0.1)  # arbitrary short time
        if self.connect_exception is not None:
            raise self.connect_exception
        self.connected = True

    async def disconnect(self) -> None:
        await asyncio.sleep(0.1)  # arbitrary short time
        if self.disconnect_exception is not None:
            raise self.disconnect_exception
        self.connected = False

    async def run(self) -> None:
        if self.run_exception is not None:
            raise self.run_exception
        self.num_run += 1
        while True:
            await asyncio.sleep(1)  # arbitrary
