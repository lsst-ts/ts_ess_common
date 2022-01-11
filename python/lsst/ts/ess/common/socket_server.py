from __future__ import annotations

# This file is part of ts_ess_common.
#
# Developed for the Vera Rubin Observatory Telescope and Site Systems.
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

__all__ = ["SocketServer"]

import asyncio
import json
import logging
import socket
import typing

from .abstract_command_handler import AbstractCommandHandler
from lsst.ts import tcpip


class SocketServer(tcpip.OneClientServer):
    """A server for exchanging messages that talks over TCP/IP.

    Upon initiation a socket server is set up which waits for incoming
    commands. When an exit command is received, the socket server will exit.
    All other commands are dispatched to the command handler.

    Parameters
    ----------
    name : `str`
        The name of the socket server.
    host : `str` or `None`
        IP address for this server.
        If `None` then bind to all network interfaces.
    port : `int`
        IP port for this server. If 0 then use a random port.
    simulation_mode : `int`, optional
        Simulation mode. The default is 0: do not simulate.
    family : `socket.AddressFamily`
        The address family that the socket will use. The default is
        AF_UNSPEC.
    """

    valid_simulation_modes = (0, 1)

    def __init__(
        self,
        name: str,
        host: typing.Optional[str],
        port: int,
        simulation_mode: int = 0,
        family: socket.AddressFamily = socket.AF_UNSPEC,
        connect_callback: typing.Optional[typing.Callable] = None,
    ) -> None:
        self.name = name
        if simulation_mode not in self.valid_simulation_modes:
            raise ValueError(
                f"simulation_mode={simulation_mode} "
                f"not in valid_simulation_modes={self.valid_simulation_modes}"
            )

        self.simulation_mode = simulation_mode
        self.read_loop_task: asyncio.Future = asyncio.Future()
        self.log: logging.Logger = logging.getLogger(type(self).__name__)
        self.command_handler: typing.Optional[AbstractCommandHandler] = None

        if connect_callback is None:
            connect_callback = self.connect_callback

        super().__init__(
            name=self.name,
            host=host,
            port=port,
            log=self.log,
            connect_callback=connect_callback,
            family=family,
        )

    def set_command_handler(self, command_handler: AbstractCommandHandler) -> None:
        """Set the command handler instance to use. All code using
        this SocketServer class must call this at least once before
        sending commands.

        Parameters
        ----------
        command_handler : `AbstractCommandHandler`
            The command handler instance to use.
        """
        self.command_handler = command_handler

    def connect_callback(self, server: SocketServer) -> None:
        """A client has connected or disconnected."""
        if self.connected:
            self.log.info("Client connected.")
            self.read_loop_task = asyncio.create_task(self.read_loop())
        else:
            self.log.info("Client disconnected.")

    async def write(self, data: dict) -> None:
        """Write the data appended with a newline character.

        The data are encoded via JSON and then passed on to the StreamWriter
        associated with the socket.

        Parameters
        ----------
        data : `dict`
            The data to write.
        """
        self.log.debug(f"Writing data {data}")
        st = json.dumps({**data})
        self.log.debug(st)
        if self.connected:
            self.writer.write(st.encode() + tcpip.TERMINATOR)
            await self.writer.drain()
        self.log.debug("Done")

    async def read_loop(self) -> None:
        """Read commands and output replies."""
        try:
            self.log.info(f"The read_loop begins connected? {self.connected}")
            while self.connected:
                self.log.debug("Waiting for next incoming message.")
                line = await self.reader.readuntil(tcpip.TERMINATOR)
                if line:
                    line = line.decode().strip()
                    self.log.debug(f"Read command line: {line!r}")
                    items = json.loads(line)
                    cmd = items["command"]
                    kwargs = items["parameters"]
                    if cmd == "exit":
                        await self.exit()
                    elif cmd == "disconnect":
                        await self.disconnect()
                    else:
                        if self.command_handler is not None:
                            await self.command_handler.handle_command(cmd, **kwargs)

        except Exception:
            self.log.exception("read_loop failed. Disconnecting.")
            await self.disconnect()

    async def disconnect(self) -> None:
        """Stop sending telemetry and close the client."""
        if self.command_handler is not None:
            await self.command_handler.stop_sending_telemetry()
        self.log.debug("Cancelling read_loop_task.")
        self.read_loop_task.cancel()
        self.log.debug("Closing client.")
        await self.close_client()

    async def exit(self) -> None:
        """Stop the TCP/IP server."""
        self.log.info("Closing server")
        await self.close()

        self.log.info("Done closing")
