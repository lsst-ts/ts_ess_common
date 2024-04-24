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

import logging
import unittest

from lsst.ts.ess import common


class TcpipDeviceTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_tcp_ip_device(self) -> None:
        log = logging.Logger(type(self).__name__)
        num_channels = 4
        sensor = common.sensor.TemperatureSensor(log=log, num_channels=num_channels)
        tcpip_device = common.device.TcpipDevice(
            name="Test",
            host="",
            port=0,
            sensor=sensor,
            baud_rate=19200,
            callback_func=None,
            log=log,
            simulation_mode=1,
        )
        await tcpip_device.open()
        line = await tcpip_device.readline()
        line = line.decode().strip()
        line_items = line.split(",")
        assert len(line_items) == num_channels
        await tcpip_device.close()
