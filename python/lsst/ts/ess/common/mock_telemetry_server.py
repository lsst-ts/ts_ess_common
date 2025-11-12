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

__all__ = ["MockTelemetryServer", "run_mock_telemetry_server"]

import asyncio
import logging
import typing

from lsst.ts import tcpip

from .constants import Key, ResponseCode, SensorType
from .device import BaseDevice, MockDevice
from .sensor import create_sensor


MOCK_DEVICE_ID_PREFIX = "MockDevice"


class MockTelemetryServer(tcpip.OneClientReadLoopServer):
    def __init__(
        self,
        host: str | None,
        port: int | None,
        log: logging.Logger,
        device_configuration: dict[str, typing.Any],
        connect_callback: tcpip.ConnectCallbackType | None = None,
        name: str = "",
        **kwargs: typing.Any,
    ) -> None:
        super().__init__(
            host=host,
            port=port,
            log=log,
            connect_callback=connect_callback,
            name=name,
            **kwargs,
        )
        self.sensor = create_sensor(device_configuration, log=self.log)
        self.device_configuration = device_configuration
        self.device: BaseDevice = MockDevice(
            name=name,
            device_id=f"{MOCK_DEVICE_ID_PREFIX}-{name}",
            sensor=self.sensor,
            callback_func=self.callback,
            log=self.log,
        )

    async def read_and_dispatch(self) -> None:
        """Send the same data every second."""
        try:
            data = await self.device.readline()
            self.log.info(f"Sending data {data}.")
            await self.write_str(data + self.sensor.terminator)
            await asyncio.sleep(1.0)
        except (asyncio.IncompleteReadError, ConnectionResetError):
            # Ignore
            pass

    async def callback(self, response: dict[ResponseCode, typing.Any]) -> None:
        # Empty because unused.
        pass


async def run_mock_telemetry_server() -> None:
    logging.basicConfig(format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG)
    log = logging.getLogger("dummy")
    device_configuration = {
        Key.NAME.value: "MockDevice",
        Key.SENSOR_TYPE.value: SensorType.TEMPERATURE,
        Key.CHANNELS.value: 4,
    }
    srv = MockTelemetryServer(host="0.0.0.0", port=4001, log=log, device_configuration=device_configuration)
    await srv.start_task
    await srv._server.serve_forever()
