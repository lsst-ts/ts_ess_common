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

__all__ = ["BaseReadLoopDataClient"]

import abc
import asyncio
import logging
import types
from typing import TYPE_CHECKING

from .base_data_client import BaseDataClient

if TYPE_CHECKING:
    from lsst.ts import salobj


class BaseReadLoopDataClient(BaseDataClient, abc.ABC):
    """Base class to read environmental data from a server and publish it
    as ESS telemetry.

    A read loop is used that captures any errors and retries before propagating
    the errors.

    Parameters
    ----------
    name : `str`
    config : `types.SimpleNamespace`
        The configuration, after validation by the schema returned
        by `get_config_schema` and conversion to a types.SimpleNamespace.
    topics : `salobj.Controller`
        The telemetry topics this model can write, as a struct with attributes
        such as ``tel_temperature``.
    log : `logging.Logger`
        Logger.
    simulation_mode : `int`, optional
        Simulation mode; 0 for normal operation.
    auto_reconnect : `bool`
        Automatically disconnect and reconnect in case of a read error
        (default: False)?

    Notes
    -----
    The config is required to contain "max_read_timeouts". If it doesn't, a
    RuntimeError is raised at instantiation.
    """

    def __init__(
        self,
        config: types.SimpleNamespace,
        topics: salobj.Controller | types.SimpleNamespace,
        log: logging.Logger,
        simulation_mode: int = 0,
        auto_reconnect: bool = False,
    ) -> None:
        super().__init__(
            config=config, topics=topics, log=log, simulation_mode=simulation_mode
        )
        if "max_read_timeouts" not in vars(config):
            raise RuntimeError("'max_read_timeouts' is required in 'config'.")

        self.num_consecutive_read_timeouts = 0
        self.num_reconnects = 0
        self.auto_reconnect = auto_reconnect
        self._connected = False

    @property
    def connected(self) -> bool:
        return self._connected

    async def connect(self) -> None:
        self._connected = True

    async def disconnect(self) -> None:
        self._connected = False

    async def start(self) -> None:
        """Override start method to handle auto reconnecting if necessary."""
        self.num_reconnects = 0
        await self.start_tasks()
        if self.auto_reconnect:
            while self.num_reconnects < 5:
                self.num_reconnects += 1
                await self.stop_tasks()
                await self.start_tasks()

    async def run(self) -> None:
        try:
            await self.read_loop()
        except asyncio.CancelledError:
            self.log.warning("Task was canceled so not raising the exception.")
        except asyncio.InvalidStateError:
            self.log.warning("Task is still running so not raising the exception.")

    async def read_loop(self) -> None:
        """Call the read_data method in a loop.

        Allow for max_timeouts timeouts before raising a TimeoutError.
        """
        await self.setup_reading()
        # Number of consecutive read timeouts encountered.
        self.num_consecutive_read_timeouts = 0
        while self.connected:
            await self.read_data_once()

    async def read_data_once(self) -> None:
        try:
            await self.read_data()
            self.num_consecutive_read_timeouts = 0
        except asyncio.TimeoutError:
            self.num_consecutive_read_timeouts += 1

            if self.num_consecutive_read_timeouts >= self.config.max_read_timeouts:
                self.log.error(
                    f"Read timed out {self.num_consecutive_read_timeouts} times "
                    f">= {self.config.max_read_timeouts=}; giving up."
                )
                raise

            message = (
                f"Read timed out. This is timeout #{self.num_consecutive_read_timeouts} "
                f"of {self.config.max_read_timeouts} allowed."
            )
            if self.auto_reconnect:
                message += " Attempting to disconnect and reconnect now."
            self.log.warning(message)

            if self.auto_reconnect:
                await self.disconnect()
        except StopIteration:
            self.log.info("read loop ends: out of simulated raw data")
        except Exception as e:
            self.log.exception(f"read loop failed: {e!r}")
            raise

    async def setup_reading(self) -> None:
        """Perform any tasks before starting the read loop."""
        pass

    @abc.abstractmethod
    async def read_data(self) -> None:
        """Read data.

        Notes
        -----
        This method needs to raise an `asyncio.TimeoutError` when timing out,
        otherwise the `read_loop` method may hang forever.
        """
        raise NotImplementedError()
