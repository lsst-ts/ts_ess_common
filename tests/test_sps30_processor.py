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
import random
import types
import unittest
from unittest.mock import AsyncMock

from lsst.ts.ess import common


class Sps30ProcessorTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_processor(self) -> None:
        device_configuration = common.DeviceConfig(
            name="TestDevice",
            dev_type=common.DeviceType.FTDI,
            dev_id="ABCDEF",
            sens_type=common.SensorType.SPS30,
            baud_rate=9600,
            location="Test1",
        )
        evt_sensor_status = AsyncMock()
        tel_particleMeasurements = AsyncMock()
        topics = types.SimpleNamespace(
            evt_sensorStatus=evt_sensor_status, tel_particleMeasurements=tel_particleMeasurements
        )
        log = logging.getLogger()
        processor = common.processor.Sps30Processor(device_configuration, topics, log)

        timestamp = 12345.0
        response_code = 0
        particle_sizes = common.PARTICLE_SIZES
        particle_concentrations = [
            random.uniform(
                common.device.MockParticleConcentrationConfig.min,
                common.device.MockParticleConcentrationConfig.max,
            )
            for _ in range(5)
        ]
        particle_number_concentrations = [
            random.uniform(
                common.device.MockParticleNumberConcentrationConfig.min,
                common.device.MockParticleNumberConcentrationConfig.max,
            )
            for _ in range(5)
        ]
        typicle_particle_size = random.uniform(
            common.device.MockParticleSizeConfig.min,
            common.device.MockParticleSizeConfig.max,
        )
        sensor_data = (
            ["_"]
            + [timestamp]
            + particle_sizes
            + particle_concentrations
            + particle_number_concentrations
            + [typicle_particle_size]
            + ["_"]
        )

        await processor.process_telemetry(
            timestamp=timestamp,
            response_code=response_code,
            sensor_data=sensor_data,
        )
        evt_sensor_status.set_write.assert_called_with(
            sensorName=device_configuration.name, sensorStatus=0, serverStatus=0
        )
        tel_particleMeasurements.set_write.assert_called_with(
            sensorName=device_configuration.name,
            timestamp=timestamp,
            particleSizes=particle_sizes,
            matterConcentration=particle_concentrations,
            numberConcentration=particle_number_concentrations,
            typicalParticleSize=typicle_particle_size,
            location=device_configuration.location,
        )
