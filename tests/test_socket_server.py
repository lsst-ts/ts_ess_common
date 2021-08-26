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

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)

# Standard timeout in seconds.
TIMEOUT = 5


class SocketServerTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.ctrl = None
        self.writer = None
        self.mock_ctrl = None
        self.name = "MockDevice"
        self.srv = None
        self.srv = common.SocketServer(
            name="EssCommonTest", host="0.0.0.0", port=0, simulation_mode=1
        )
        mock_command_handler = common.MockCommandHandler(
            callback=self.srv.write, simulation_mode=1, name=self.name
        )
        self.srv.set_command_handler(mock_command_handler)

        self.log = logging.getLogger(type(self).__name__)

        await self.srv.start_task
        self.assertTrue(self.srv.server.is_serving())
        self.reader, self.writer = await asyncio.open_connection(
            host=tcpip.LOCAL_HOST, port=self.srv.port
        )

    async def asyncTearDown(self) -> None:
        assert self.srv is not None
        await self.srv.disconnect()
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        await self.srv.exit()

    async def read(self) -> typing.Dict[str, typing.Any]:
        """Read a string from the reader and unmarshal it.

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

    async def test_disconnect(self) -> None:
        assert self.srv is not None
        self.assertTrue(self.srv.connected)
        await self.write(command=common.Command.DISCONNECT, parameters={})
        # Give time to the socket server to clean up internal state and exit.
        await asyncio.sleep(0.5)
        self.assertFalse(self.srv.connected)

    async def test_exit(self) -> None:
        assert self.srv is not None
        self.assertTrue(self.srv.connected)
        await self.write(command=common.Command.EXIT, parameters={})
        # Give time to the socket server to clean up internal state and exit.
        await asyncio.sleep(0.5)
        self.assertFalse(self.srv.connected)

    def check_temperature_reply(
        self, reply: typing.List[typing.Union[str, float]], num_channels: int
    ) -> None:
        device_name = reply[0]
        time = reply[1]
        response_code = reply[2]
        resp = reply[3:]

        self.assertEqual(self.name, device_name)
        self.assertGreater(time, 0)
        self.assertEqual(common.ResponseCode.OK, response_code)
        self.assertEqual(len(resp), num_channels)
        for i in range(0, num_channels):
            self.assertLessEqual(common.MockTemperatureConfig.min, resp[i])
            self.assertLessEqual(resp[i], common.MockTemperatureConfig.max)

    async def check_server_test(self, num_channels: int) -> None:
        """Test a full command sequence of the SocketServer.

        Parameters
        ----------
        num_channels: `int`
            The number of channels for which temperature data are
            expected.

        Notes
        -----
        The sequence of commands is
            - configure
            - start
            - read telemetry
            - stop
            - disconnect
            - exit

        The MockCommandHandler is used which always outputs 4
        temperature values. Also, simulation_mode is set to 1 meaning
        that the DeviceType and SensorType are ignored when creating
        the mock output. However, the configuration gets validated
        which is why the configuration below is used.
        """
        self.assertEqual(num_channels, 4)
        configuration = {
            common.Key.DEVICES: [
                {
                    common.Key.NAME: self.name,
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
        self.assertEqual(common.ResponseCode.OK, data[common.Key.RESPONSE])
        await self.write(command=common.Command.START, parameters={})
        data = await self.read()
        self.assertEqual(common.ResponseCode.OK, data[common.Key.RESPONSE])

        reply = await self.read()
        reply_to_check = reply[common.Key.TELEMETRY]
        self.check_temperature_reply(reply=reply_to_check, num_channels=num_channels)

        reply = await self.read()
        reply_to_check = reply[common.Key.TELEMETRY]
        self.check_temperature_reply(reply=reply_to_check, num_channels=num_channels)

        await self.write(command=common.Command.STOP, parameters={})
        data = await self.read()
        self.assertEqual(common.ResponseCode.OK, data[common.Key.RESPONSE])
        await self.write(command=common.Command.DISCONNECT, parameters={})
        await self.write(command=common.Command.EXIT, parameters={})

    async def test_full_command_sequence(self) -> None:
        """Test the SocketServer with a nominal configuration, i.e. no
        disconnected channels and no truncated data.
        """
        await self.check_server_test(num_channels=4)
