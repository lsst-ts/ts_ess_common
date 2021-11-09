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
import json
import logging
import typing
import unittest

from lsst.ts import tcpip
from lsst.ts.ess import common

# Standard timeout in seconds.
TIMEOUT = 5


class SocketServerTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.writer = None
        self.srv = common.SocketServer(
            name="EssSensorsServer",
            host="0.0.0.0",
            port=0,
            simulation_mode=1,
            connect_callback=self.connect_callback,
        )
        command_handler = common.MockCommandHandler(
            callback=self.srv.write, simulation_mode=1
        )
        self.srv.set_command_handler(command_handler)

        self.log = logging.getLogger(type(self).__name__)

        self.connected_future: asyncio.Future = asyncio.Future()
        await self.srv.start_task
        assert self.srv.server.is_serving()
        self.reader, self.writer = await asyncio.open_connection(
            host=tcpip.LOCAL_HOST, port=self.srv.port
        )
        # Give time to the socket server to respond.
        await self.connected_future
        assert self.srv.connected
        self.log.info("===== End of asyncSetUp =====")

    async def asyncTearDown(self) -> None:
        self.log.info("===== Start of asyncTearDown =====")
        await self.srv.disconnect()
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        await self.srv.exit()

    async def read(self) -> typing.Dict[str, typing.Any]:
        """Read a string from the reader and unmarshal it

        Returns
        -------
        data : `dict`
            A dictionary with objects representing the string read.
        """
        read_bytes = await asyncio.wait_for(
            self.reader.readuntil(tcpip.TERMINATOR), timeout=TIMEOUT
        )
        data = json.loads(read_bytes.decode())
        return data

    async def write(self, **data: typing.Dict[str, typing.Any]) -> None:
        """Write the data appended with a tcpip.TERMINATOR string.

        Parameters
        ----------
        data:
            The data to write.
        """
        st = json.dumps({**data})
        assert self.writer is not None
        self.writer.write(st.encode() + tcpip.TERMINATOR)
        await self.writer.drain()

    def connect_callback(self, server: common.SocketServer) -> None:
        if not self.connected_future.done():
            self.connected_future.set_result(server.connected)
            self.srv.connect_callback(server)

    async def test_disconnect(self) -> None:
        self.connected_future = asyncio.Future()
        assert self.srv.connected
        await self.write(command=common.Command.DISCONNECT, parameters={})
        # Give time to the socket server to clean up internal state and exit.
        await self.connected_future
        assert not self.srv.connected

    async def test_exit(self) -> None:
        self.connected_future = asyncio.Future()
        assert self.srv.connected
        await self.write(command=common.Command.EXIT, parameters={})
        # Give time to the socket server to clean up internal state and exit.
        await self.connected_future
        assert not self.srv.connected

    async def check_server_test(
        self,
        name: str,
        num_channels: int = 0,
        disconnected_channel: int = -1,
        missed_channels: int = 0,
        in_error_state: bool = False,
    ) -> None:
        """Test a full command sequence of the SocketServer.

        The sequence is
            - configure
            - start
            - read telemetry
            - stop
            - disconnect
            - exit
        """
        mtt = common.MockTestTools()
        configuration = {
            common.Key.DEVICES: [
                {
                    common.Key.NAME: name,
                    common.Key.CHANNELS: num_channels,
                    common.Key.DEVICE_TYPE: common.DeviceType.FTDI,
                    common.Key.FTDI_ID: "ABC",
                    common.Key.SENSOR_TYPE: common.SensorType.TEMPERATURE,
                }
            ]
        }
        await self.write(
            command=common.Command.CONFIGURE,
            parameters={common.Key.CONFIGURATION: configuration},
        )
        data = await self.read()
        assert common.ResponseCode.OK == data[common.Key.RESPONSE]
        await self.write(command=common.Command.START, parameters={})
        data = await self.read()
        assert common.ResponseCode.OK == data[common.Key.RESPONSE]

        # Make sure that the mock sensor outputs data for a disconnected
        # channel.
        self.srv.command_handler.devices[0].disconnected_channel = disconnected_channel

        # Make sure that the mock sensor outputs truncated data.
        self.srv.command_handler.devices[0].missed_channels = missed_channels

        # Make sure that the mock sensor is in error state.
        self.srv.command_handler.devices[0].in_error_state = in_error_state

        self.reply = await self.read()
        reply_to_check = self.reply[common.Key.TELEMETRY]
        mtt.check_temperature_reply(
            reply=reply_to_check,
            name=name,
            num_channels=num_channels,
            disconnected_channel=disconnected_channel,
            missed_channels=missed_channels,
            in_error_state=in_error_state,
        )

        # Reset self.missed_channels and read again. The data should not be
        # truncated anymore.
        missed_channels = 0

        self.reply = await self.read()
        reply_to_check = self.reply[common.Key.TELEMETRY]
        mtt.check_temperature_reply(
            reply=reply_to_check,
            name=name,
            num_channels=num_channels,
            disconnected_channel=disconnected_channel,
            missed_channels=missed_channels,
            in_error_state=in_error_state,
        )

        await self.write(command=common.Command.STOP, parameters={})
        data = await self.read()
        assert common.ResponseCode.OK == data[common.Key.RESPONSE]
        await self.write(command=common.Command.DISCONNECT, parameters={})
        await self.write(command=common.Command.EXIT, parameters={})

    async def test_full_command_sequence(self) -> None:
        """Test the SocketServer with a nominal configuration, i.e. no
        disconnected channels and no truncated data.
        """
        await self.check_server_test(name="Test1", num_channels=1)

    async def test_full_command_sequence_with_disconnected_channel(self) -> None:
        """Test the SocketServer with one disconnected channel and no truncated
        data.
        """
        await self.check_server_test(
            name="Test1", num_channels=4, disconnected_channel=1
        )

    async def test_full_command_sequence_with_truncated_output(self) -> None:
        """Test the SocketServer with no disconnected channels and truncated
        data for two channels.
        """
        await self.check_server_test(name="Test1", num_channels=4, missed_channels=2)

    async def test_full_command_sequence_in_error_state(self) -> None:
        """Test the SocketServer with a sensor in error state, meaning it will
        only output empty strings.
        """
        await self.check_server_test(name="Test1", num_channels=4, in_error_state=True)
