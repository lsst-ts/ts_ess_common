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

from __future__ import annotations

__all__ = ["MockController"]

import logging
import typing

from lsst.ts import tcpip

from .abstract_command_handler import AbstractCommandHandler
from .constants import Command, Key


class MockController(tcpip.OneClientReadLoopServer):
    """A mock controller for exchanging JSON messages via TCP/IP.

    See ``tcpip.OneClientReadLoopServer`` for the inner workings.

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
    """

    valid_simulation_modes = (0, 1)

    def __init__(
        self,
        name: str,
        host: None | str,
        port: int,
        log: logging.Logger,
        simulation_mode: int = 0,
        connect_callback: None | tcpip.ConnectCallbackType = None,
    ) -> None:
        self.name = name
        if simulation_mode not in self.valid_simulation_modes:
            raise ValueError(
                f"simulation_mode={simulation_mode} "
                f"not in valid_simulation_modes={self.valid_simulation_modes}"
            )

        self.log = logging.getLogger(type(self).__name__)
        self.simulation_mode = simulation_mode
        self.command_handler: None | AbstractCommandHandler = None

        super().__init__(
            port=port,
            host=host,
            log=self.log,
            connect_callback=connect_callback,
            name=self.name,
        )

    def set_command_handler(self, command_handler: AbstractCommandHandler) -> None:
        """Set the command handler instance to use. All code using
        this MockController class must call this at least once before
        sending commands.

        Parameters
        ----------
        command_handler : `AbstractCommandHandler`
            The command handler instance to use.
        """
        self.command_handler = command_handler

    async def read_and_dispatch(self) -> None:
        items = await self.read_json()
        cmd = items[Key.COMMAND]
        kwargs = items[Key.PARAMETERS]
        if cmd == Command.EXIT:
            await self.exit()
        elif cmd == Command.DISCONNECT:
            await self.close_client()
        else:
            if self.command_handler is not None:
                await self.command_handler.handle_command(cmd, **kwargs)

    async def close_client(self, **kwargs: typing.Any) -> None:
        """Stop sending telemetry and close the client."""
        if self.command_handler is not None:
            await self.command_handler.stop_sending_telemetry()
        await super().close_client(**kwargs)
