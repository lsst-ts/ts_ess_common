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

__all__ = [
    "DEFAULT_RATE_LIMIT",
    "BaseReadLoopDataClient",
    "get_data_client_class",
]

import abc
import asyncio
import importlib
import inspect
import logging
import types
import typing
from typing import TYPE_CHECKING

from lsst.ts import utils

if TYPE_CHECKING:
    from lsst.ts import salobj

# Default maximum number of read timeouts.
DEFAULT_MAX_READ_TIMEOUTS = 5

# Default connect timeout [sec].
DEFAULT_CONNECT_TIMEOUT = 60

# Default read timeout [sec].
DEFAULT_READ_TIMEOUT = 60

# Telemetry rate limit [s] to prevent excessive error messages.
DEFAULT_RATE_LIMIT = 1.0

# The minimum telemetry rate limit [s] to prevent excessive error messages.
# This value limits the error messages to 20 Hz.
MIN_RATE_LIMIT = 0.05

# Telemetry loop finish timeout [s].
TELEMETRY_LOOP_FINISH_TIMEOUT = 5.0

# Dict of data client class name: data client class.
# Access via the `get_data_client_class functions`.
# BaseDataClient automatically registers concrete subclasses.
_DataClientClassRegistry: dict[str, typing.Type[BaseReadLoopDataClient]] = dict()

# Dict of data client class name: name of module in which it is defined.
# You may omit data clients found in ts_ess_common and ts_ess_csc,
# because the ESS CSC already imports those two modules.
ExternalDataClientModules = dict(
    EarthquakeDataClient="lsst.ts.ess.earthquake",
    LabJackDataClient="lsst.ts.ess.labjack",
    LabJackAccelerometerDataClient="lsst.ts.ess.labjack",
    RingssDataClient="lsst.ts.ess.ringss",
    ModbusDataClient="lsst.ts.ess.epm",
    SnmpDataClient="lsst.ts.ess.epm",
)


def get_data_client_class(class_name: str) -> typing.Type[BaseReadLoopDataClient]:
    """Get a data client class by class name.

    Parameters
    ----------
    class_name : `str`
        Name of data client class, e.g. "MockDataClient".

    Raises
    ------
    KeyError
        If the specified class is not in the registry.
    """
    global _DataClientClassRegistry
    global ExternalDataClientModules
    module_name = ExternalDataClientModules.get(class_name)
    if module_name is not None:
        importlib.import_module(module_name)
    return _DataClientClassRegistry[class_name]


class BaseReadLoopDataClient(abc.ABC):
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
    ) -> None:
        self.config = config
        self.topics = topics
        self.log = log.getChild(type(self).__name__)
        self.simulation_mode = simulation_mode

        self.run_task = utils.make_done_future()
        self.loop_should_end = False

        self.max_read_timeouts = getattr(self.config, "max_read_timeouts", DEFAULT_MAX_READ_TIMEOUTS)

        self.connect_timeout = getattr(self.config, "connect_timeout", DEFAULT_CONNECT_TIMEOUT)

        self.read_timeout = getattr(self.config, "read_timeout", DEFAULT_READ_TIMEOUT)

        self.num_consecutive_read_timeouts = 0
        self._connected = False
        self.timeout_event = asyncio.Event()

        # Set the configured rate limit if present and make sure it is not
        # too small. Use the default rate limit if not in the configuration.
        self.rate_limit = max(MIN_RATE_LIMIT, getattr(self.config, "rate_limit", DEFAULT_RATE_LIMIT))

    @classmethod
    @abc.abstractmethod
    def get_config_schema(cls) -> dict[str, typing.Any]:
        """Get the config schema as jsonschema dict."""
        raise NotImplementedError()

    @abc.abstractmethod
    def descr(self) -> str:
        """Return a brief description, without the class name.

        This should be just enough information to distinguish
        one instance of this client from another.
        """
        raise NotImplementedError()

    @property
    def connected(self) -> bool:
        return self._connected

    async def connect(self) -> None:
        self._connected = True

    async def disconnect(self) -> None:
        self._connected = False

    async def start(self) -> None:
        """Start the run task."""
        self.loop_should_end = False
        self.run_task = asyncio.create_task(self.run())

    async def run(self) -> None:
        """Perform the life cycle of a DtaClient in a loop.

        The life cycle is:

          - connect
          - setup reading
          - read data while connected
          - handle exceptions
          - disconnect
        """
        self.num_consecutive_read_timeouts = 0
        self.timeout_event.clear()
        while not self.loop_should_end:
            try:
                if not self.connected:
                    self.log.debug("Trying to connect.")
                    await self.connect()
                await self.setup_reading()
                self.log.debug(f"{self.connected=}, {self.loop_should_end=}")
                while self.connected and not self.loop_should_end:
                    rate_limit_task = asyncio.create_task(asyncio.sleep(self.rate_limit))
                    try:
                        await self.read_data()
                        self.num_consecutive_read_timeouts = 0
                        self.timeout_event.clear()
                    finally:
                        await rate_limit_task
            except asyncio.CancelledError:
                self.loop_should_end = True
            except Exception as e:
                self.num_consecutive_read_timeouts += 1
                if self.num_consecutive_read_timeouts >= self.max_read_timeouts:
                    self.log.error(
                        f"Read timed out {self.num_consecutive_read_timeouts} times "
                        f">= {self.max_read_timeouts=}; giving up. Raising {e!r}."
                    )
                    self.loop_should_end = True
                    self.timeout_event.set()
                    raise

                message = (
                    f"Read timed out. This is timeout #{self.num_consecutive_read_timeouts} "
                    f"of {self.max_read_timeouts} allowed. Error was: {e!r}. "
                    f"Attempting to reconnect in {self.connect_timeout} seconds."
                )
                self.loop_should_end = False
                self.log.warning(message)
            finally:
                self.log.debug("finally...")
                await self.disconnect()
                if not self.loop_should_end:
                    await asyncio.sleep(self.connect_timeout)

        self.log.info("End of DataClient life cycle. Goodbye.")

    async def setup_reading(self) -> None:
        """Perform any tasks before starting the read loop."""
        pass

    @abc.abstractmethod
    async def read_data(self) -> None:
        """Read data.

        Notes
        -----
        This method needs to raise an `TimeoutError` when timing out,
        otherwise the `read_loop` method may hang forever.
        """
        raise NotImplementedError()

    async def stop(self) -> None:
        """Stop reading and publishing data.

        This is alway safe to call, whether connected or not.
        This should raise no exceptions except asyncio.CancelledError.
        If `disconnect` raises, this logs the exception and continues.
        """
        self.log.debug("Stop called.")
        self.loop_should_end = True

        try:
            async with asyncio.timeout(TELEMETRY_LOOP_FINISH_TIMEOUT):
                await self.run_task
        except TimeoutError:
            self.log.exception("Failed to close run task in time alloted.")
        except (Exception, asyncio.CancelledError):
            self.log.exception("Something went wrong so closing run task.")
        finally:
            notyet_cancelled = self.run_task.cancel()
            if notyet_cancelled:
                await self.run_task

    def __repr__(self) -> str:
        """Return a repr of this data client.

        Subclasses may wish to override to add more information,
        such as host and port.
        """
        try:
            descr = self.descr()
        except Exception:
            descr = "?"
        return f"{type(self).__name__}({descr})"

    @classmethod
    def __init_subclass__(cls) -> None:
        """Register concrete subclasses."""
        global _DataClientClassRegistry
        if inspect.isabstract(cls):
            # Will not add abstract classes.
            pass
        name = cls.__name__
        _DataClientClassRegistry[name] = cls

    async def __aenter__(self) -> BaseReadLoopDataClient:
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: typing.Type[BaseException] | None,
        value: BaseException | None,
        traceback: types.TracebackType | None,
    ) -> None:
        await self.stop()
