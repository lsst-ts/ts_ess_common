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

import contextlib
import typing

from lsst.ts import tcpip
from lsst.ts.ess import common
from lsst.ts.ess.common.test_utils import MockTestTools

# Standard timeout in seconds.
TIMEOUT = 60


class SocketServerTestCase(tcpip.BaseOneClientServerTestCase):
    server_class = common.SocketServer

    @contextlib.asynccontextmanager
    async def create_server_with_command_handler(
        self,
    ) -> typing.AsyncGenerator[common.SocketServer, None]:
        async with self.create_server(
            name="EssSensorsServer",
            host=tcpip.DEFAULT_LOCALHOST,
            simulation_mode=1,
            connect_callback=self.connect_callback,
        ) as server:
            command_handler = common.MockCommandHandler(
                callback=server.write_json, simulation_mode=1
            )
            server.set_command_handler(command_handler)
            yield server

    async def assert_configure(
        self,
        client: tcpip.Client,
        name: str,
        num_channels: int = 0,
        disconnected_channel: int = -1,
        missed_channels: int = 0,
        in_error_state: bool = False,
    ) -> None:
        configuration = {
            common.Key.DEVICES: [
                {
                    common.Key.NAME: name,
                    common.Key.CHANNELS: num_channels,
                    common.Key.DEVICE_TYPE: common.DeviceType.FTDI,
                    common.Key.FTDI_ID: "ABC",
                    common.Key.SENSOR_TYPE: common.SensorType.TEMPERATURE,
                    common.Key.BAUD_RATE: 19200,
                }
            ]
        }
        await client.write_json(
            data={
                common.JsonKeys.COMMAND: common.Command.CONFIGURE,
                common.JsonKeys.PARAMETERS: {common.Key.CONFIGURATION: configuration},
            }
        )
        data = await client.read_json()
        assert common.ResponseCode.OK == data[common.Key.RESPONSE]

    async def test_disconnect(self) -> None:
        async with self.create_server_with_command_handler() as server, self.create_client(
            server
        ) as client:
            await self.assert_next_connected(True)
            await self.assert_configure(client=client, name="TEST_DISCONNECT")
            await client.write_json(
                data={
                    common.JsonKeys.COMMAND: common.Command.DISCONNECT,
                    common.JsonKeys.PARAMETERS: {},
                }
            )
            await self.assert_next_connected(False)
            assert not server.connected
            assert not client.connected

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
        mtt = MockTestTools()
        async with self.create_server_with_command_handler() as server, self.create_client(
            server
        ) as client:
            await self.assert_configure(
                client=client,
                name=name,
                num_channels=num_channels,
                disconnected_channel=disconnected_channel,
                missed_channels=missed_channels,
                in_error_state=in_error_state,
            )

            # Make sure that the mock sensor outputs data for a disconnected
            # channel.
            server.command_handler.devices[
                0
            ].disconnected_channel = disconnected_channel

            # Make sure that the mock sensor outputs truncated data.
            server.command_handler.devices[0].missed_channels = missed_channels

            # Make sure that the mock sensor is in error state.
            server.command_handler.devices[0].in_error_state = in_error_state

            reply = await client.read_json()
            reply_to_check = reply[common.Key.TELEMETRY]
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

            reply = await client.read_json()
            reply_to_check = reply[common.Key.TELEMETRY]
            mtt.check_temperature_reply(
                reply=reply_to_check,
                name=name,
                num_channels=num_channels,
                disconnected_channel=disconnected_channel,
                missed_channels=missed_channels,
                in_error_state=in_error_state,
            )

            await client.write_json(
                data={
                    common.JsonKeys.COMMAND: common.Command.DISCONNECT,
                    common.JsonKeys.PARAMETERS: {},
                }
            )

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
