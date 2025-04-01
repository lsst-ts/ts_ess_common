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
    "BaseDataClient",
    "get_data_client_class",
]

import abc
import asyncio
import importlib
import inspect
import logging
import types
import typing

if typing.TYPE_CHECKING:
    from lsst.ts import salobj

from lsst.ts import utils

# Dict of data client class name: data client class.
# Access via the `get_data_client_class functions`.
# BaseDataClient automatically registers concrete subclasses.
_DataClientClassRegistry: dict[str, typing.Type[BaseDataClient]] = dict()

# Dict of data client class name: name of module in which it is defined.
# You may omit data clients found in ts_ess_common and ts_ess_csc,
# because the ESS CSC already imports those two modules.
ExternalDataClientModules = dict(
    EarthquakeDataClient="lsst.ts.ess.earthquake",
    LabJackDataClient="lsst.ts.ess.labjack",
    LabJackAccelerometerDataClient="lsst.ts.ess.labjack",
    RingssDataClient="lsst.ts.ess.ringss",
    ModbusDataClient="lsst.ts.ess.epm",
)


def get_data_client_class(class_name: str) -> typing.Type[BaseDataClient]:
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


class BaseDataClient(abc.ABC):
    """Base class to read environmental data from a server and publish it
    as ESS telemetry.

    Automatically add concrete subclasses to a registry, where they can be
    retrieved using the `get_data_client_class` function.

    If you add a data client to a package other than ``ts_ess_common``
    or ``ts_ess_csc``, then you must also add an entry to
    `ExternalDataClientModules`. That allows this code to dynamically
    import the module (which registers the data client class).

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
        self.connect_task = utils.make_done_future()
        self.run_task = utils.make_done_future()
        self.disconnect_task = utils.make_done_future()
        self.log = log.getChild(type(self).__name__)
        self.simulation_mode = simulation_mode

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
        For example RPiDataClient should return something like::

           f"host={self.config.host}, port={self.config.port}"
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def connect(self) -> None:
        """Connect to the data server.

        This will not be called if already connected.
        See the Raises section for exceptions subclasses should raise.

        Raises
        ------
        ConnectionError
            If the data server rejects the connection.
            This may happen if the data server is down
            or the configuration specified an invalid address.
        asyncio.TimeoutError
            If a connection cannot be made in reasonable time.
        Exception
            (or any subclass) if any other serious problem occurs.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the data server.

        This must always be safe to call, whether connected or not.
        """
        raise NotImplementedError()

    async def start(self) -> None:
        """Delegate handling of start tasks to the start_tasks method.

        This allows implementing classes to customize start behavior.
        """
        await self.start_tasks()

    async def start_tasks(self) -> None:
        """Call disconnect, connect, and start the run task.

        Raises the same exceptions as `connect`.
        If `disconnect` raises, this logs the exception and continues.
        """
        self.connect_task.cancel()
        self.disconnect_task.cancel()
        try:
            await self.disconnect()
        except Exception:
            self.log.exception(
                "Could not disconnect before connecting. Trying to connect anyway."
            )
        await self.connect()
        self.run_task = asyncio.create_task(self.run())

    @abc.abstractmethod
    async def run(self) -> None:
        """Read data from the server and publish it as ESS telemetry.

        This is called once after `connect` and it should keep running
        until cancelled.
        See the Raises section for exceptions subclasses should raise.

        Raises
        ------
        ConnectionError
            If the connection to the data server is lost.
        asyncio.TimeoutError
            If data is not received in reasonable time.
        Exception
            (or any subclass) if any other serious problem occurs.
        """
        raise NotImplementedError()

    async def stop(self) -> None:
        """Delegate handling of stop tasks to the stop_tasks method.

        This allows implementing classes to customize stop behavior.
        """
        await self.stop_tasks()

    async def stop_tasks(self) -> None:
        """Stop reading and publishing data.

        This is alway safe to call, whether connected or not.
        This should raise no exceptions except asyncio.CancelledError.
        If `disconnect` raises, this logs the exception and continues.
        """
        self.run_task.cancel()
        try:
            await self.disconnect()
        except Exception:
            self.log.exception("Could not disconnect in stop_tasks. Continuing.")

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

    async def __aenter__(self) -> BaseDataClient:
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: typing.Type[BaseException] | None,
        value: BaseException | None,
        traceback: types.TracebackType | None,
    ) -> None:
        await self.stop()
