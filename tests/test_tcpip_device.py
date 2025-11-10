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
import logging
import unittest

from lsst.ts.ess import common


class TcpipDeviceTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_tcp_ip_device(self) -> None:
        self.log = logging.Logger(type(self).__name__)
        self.data_event = asyncio.Event()
        num_channels = 4
        sensor = common.sensor.TemperatureSensor(log=self.log, num_channels=num_channels)
        tcpip_device = common.device.TcpipDevice(
            name="Test",
            host="",
            port=0,
            sensor=sensor,
            baud_rate=19200,
            callback_func=self.process_telemetry,
            log=self.log,
            simulation_mode=1,
        )
        await tcpip_device.open()
        await tcpip_device.readline()
        await self.data_event.wait()
        telemetry = self.data[common.Key.TELEMETRY][common.Key.SENSOR_TELEMETRY]
        assert len(telemetry) == num_channels
        await tcpip_device.close()

    async def process_telemetry(self, data: dict) -> None:
        self.log.debug(f"Received {data=}")
        self.data = data
        self.data_event.set()
