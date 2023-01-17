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
import math
import unittest
from dataclasses import dataclass

import numpy as np
import pytest
from lsst.ts.ess import common

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)

# Data for the Campbell CSAT3B sensor from page 55 of csat3b.pdf.
CSAT3B_DATA = [
    "0.08945,0.06552,0.05726,19.69336,0,5,c3a6",
    "0.10103,0.06517,0.05312,19.70499,0,6,3927",
    "0.09045,0.04732,0.04198,19.71161,0,7,d7e5",
    "0.08199,0.03341,0.03421,19.73416,0,8,4ad9",
    "0.08867,0.03522,0.03378,19.75360,0,9,e314",
    "0.08675,0.02142,0.03289,19.76858,0,10,9b60",
    "0.09035,0.01987,0.03667,19.78433,0,11,931a",
    "0.09960,0.02615,0.04330,19.79236,0,12,14a1",
    "0.09489,0.02513,0.05120,19.79083,0,13,0c0d",
    "0.09513,0.02403,0.05648,19.79037,0,14,c30d",
    "0.10715,0.02723,0.05739,19.78729,0,15,a14c",
    "0.11630,0.03674,0.05579,19.78812,0,16,5cD7",
]

# Data for the Windsonic sensor.
WINDSONIC_DATA_LIST = [
    ["015.00", "010"],
    ["001.00", ""],
    ["015.00", "010"],
]

# Alias for the type of the sensor data.
SensorDataType = dict[str, common.TelemetryDataType]


@dataclass
class SensorAndData:
    sensor: common.sensor.BaseSensor
    data: SensorDataType


class AllSensorsTestCase(unittest.IsolatedAsyncioTestCase):
    def verify_float(self, reply: float, expected_reply: float) -> None:
        if math.isnan(expected_reply):
            assert math.isnan(reply)
        else:
            assert math.isclose(expected_reply, reply, abs_tol=0.005)

    async def verify_sensor_telemetry(
        self, reply: common.TelemetryDataType, sensor_data: common.TelemetryDataType
    ) -> None:
        for index, expected_reply in enumerate(sensor_data):
            if isinstance(expected_reply, float):
                self.verify_float(reply[index], expected_reply)
            else:
                assert expected_reply == reply[index]

    async def verify_all_sensor_telemetry(self) -> None:
        """Verify the sensor telemetry.

        Loop over a list of sensors and loop over the provided data to verify
        that the sensor performs as expected.
        """
        for sensor_and_data in self.sensor_and_data_list:
            sensor = sensor_and_data.sensor
            data = sensor_and_data.data
            for raw_telemetry in data:
                reply = await sensor.extract_telemetry(line=raw_telemetry)
                await self.verify_sensor_telemetry(reply, data[raw_telemetry])

    async def test_all_sensors(self) -> None:
        """Test all available sensors."""
        self.sensor_and_data_list: list[SensorAndData] = []
        self.log = logging.getLogger(type(self).__name__)

        await self.add_csat3b_sensor()
        await self.add_efm100c_sensor()
        await self.add_hx85a_sensor()
        await self.add_hx85ba_sensor()
        await self.add_ld250_sensor()
        await self.add_temperature_sensor()
        await self.add_wind_sensor()

        await self.verify_all_sensor_telemetry()

    async def add_efm100c_sensor(self) -> None:
        """Add an EFM100C sensor plus its data to the sensors to be tested."""
        sensor = common.sensor.Efm100cSensor(self.log)
        data: SensorDataType = {
            f"$+10.65,0*CE{sensor.terminator}": [10.65, 0.0],
            f"$+00.64,0*CD{sensor.terminator}": [0.64, 0.0],
            f"$-19.11,0*CD{sensor.terminator}": [-19.11, 0.0],
            f"$+00.00,0*CD{sensor.terminator}": [0.0, 0.0],
            f"$-11.45,1*CD{sensor.terminator}": [-11.45, 1.0],
            f"$11.45,0*CD{sensor.terminator}": [math.nan, 1.0],
            f"$+1.45,0*CD{sensor.terminator}": [math.nan, 1.0],
            "$+1.45,0*CD": [math.nan, 1.0],
        }
        sensor_and_data = SensorAndData(sensor=sensor, data=data)
        self.sensor_and_data_list.append(sensor_and_data)

    async def add_ld250_sensor(self) -> None:
        """Add an LD250 sensor plus its data to the sensors to be tested."""
        sensor = common.sensor.Ld250Sensor(self.log)
        data = {
            f"${common.LD250TelemetryPrefix.STATUS_PREFIX},0,0,0,0,000.0*42{sensor.terminator}": [
                common.LD250TelemetryPrefix.STATUS_PREFIX,
                0,
                0,
                0,
                0,
                0.0,
            ],
            f"${common.LD250TelemetryPrefix.NOISE_PREFIX}*42{sensor.terminator}": [
                common.LD250TelemetryPrefix.NOISE_PREFIX
            ],
            f"${common.LD250TelemetryPrefix.STRIKE_PREFIX},0,1,010.0*42{sensor.terminator}": [
                common.LD250TelemetryPrefix.STRIKE_PREFIX,
                0,
                1,
                10.0,
            ],
            f"$WIMSI,0,1,010.0*42{sensor.terminator}": [],
        }
        sensor_and_data = SensorAndData(sensor=sensor, data=data)
        self.sensor_and_data_list.append(sensor_and_data)

    async def add_csat3b_sensor(self) -> None:
        """Add a CSAT3B sensor plus its data to the sensors to be tested."""
        sensor = common.sensor.Csat3bSensor(self.log)
        data: SensorDataType = {
            f"0.08945,0.06552,0.05726,19.69336,0,5,c3a6{sensor.terminator}": [
                0.08945,
                0.06552,
                0.05726,
                19.69336,
                0,
                5,
                0xC3A6,
            ],
            # Test with a truncated line, which can be the case with the first
            # telemetry received after connecting to the sensor.
            f"0.06552,0.05726,19.69336,0,5,c3a6{sensor.terminator}": [
                math.nan,
                math.nan,
                math.nan,
                math.nan,
                0,
                0,
                0,
            ],
        }
        sensor_and_data = SensorAndData(sensor=sensor, data=data)
        self.sensor_and_data_list.append(sensor_and_data)

    async def add_hx85a_sensor(self) -> None:
        """Add a HX85A sensor plus its data to the sensors to be tested."""
        sensor = common.sensor.Hx85aSensor(self.log)
        data: SensorDataType = {
            f"%RH=38.86,AT°C=24.32,DP°C=9.57{sensor.terminator}": [38.86, 24.32, 9.57],
            f"86,AT°C=24.32,DP°C=9.57{sensor.terminator}": [np.nan, 24.32, 9.57],
            f"{sensor.terminator}": [np.nan, np.nan, np.nan],
        }
        sensor_and_data = SensorAndData(sensor=sensor, data=data)
        self.sensor_and_data_list.append(sensor_and_data)

        with pytest.raises(ValueError):
            line = f"%RH=38.86,AT°C=24.32,DP°C==9.57{sensor.terminator}"
            await sensor.extract_telemetry(line=line)

    async def add_hx85ba_sensor(self) -> None:
        """Add a HX85BA sensor plus its data to the sensors to be tested."""
        sensor = common.sensor.Hx85baSensor(self.log)
        data: SensorDataType = {
            f"%RH=38.86,AT°C=24.32,Pmb=911.40{sensor.terminator}": [
                38.86,
                24.32,
                911.40,
                9.42,
            ],
            f"86,AT°C=24.32,Pmb=911.40{sensor.terminator}": [
                np.nan,
                24.32,
                911.40,
                np.nan,
            ],
            f"{sensor.terminator}": [np.nan, np.nan, np.nan, np.nan],
        }
        sensor_and_data = SensorAndData(sensor=sensor, data=data)
        self.sensor_and_data_list.append(sensor_and_data)

        with pytest.raises(ValueError):
            line = f"%RH=38.86,AT°C==24.32,Pmb=911.40{sensor.terminator}"
            await sensor.extract_telemetry(line=line)

    async def add_temperature_sensor(self) -> None:
        """Add a temperature sensor plus its data to the sensors to be
        tested."""
        num_channels = 4
        sensor = common.sensor.TemperatureSensor(self.log, num_channels)
        data: SensorDataType = {}
        sensor_and_data = SensorAndData(sensor=sensor, data=data)
        self.sensor_and_data_list.append(sensor_and_data)

        # Incorrect format because of the "==" for C03.
        with pytest.raises(ValueError):
            line = f"0021.1224,C02=0021.1243,C03==0020.9992{sensor.terminator}"
            await sensor.extract_telemetry(line=line)

    async def add_wind_sensor(self) -> None:
        """Add a wind sensor plus its data to the sensors to be tested."""
        sensor = common.sensor.WindsonicSensor(self.log)
        data: SensorDataType = {}
        for wind_data in WINDSONIC_DATA_LIST:
            raw_telemetry = self.create_wind_sensor_line(
                sensor=sensor, speed=wind_data[0], direction=wind_data[1]
            )
            expected_wind_telemetry: common.TelemetryDataType = []
            for wd in wind_data:
                try:
                    expected_wind_telemetry.append(float(wd))
                except Exception:
                    expected_wind_telemetry.append(math.nan)
            data[raw_telemetry] = expected_wind_telemetry
        data[f"{sensor.terminator}"] = [math.nan, math.nan]
        sensor_and_data = SensorAndData(sensor=sensor, data=data)
        self.sensor_and_data_list.append(sensor_and_data)

    async def test_compute_csat3b_signature(self) -> None:
        """Test the computation of the CSAT3B signature."""
        log = logging.getLogger(type(self).__name__)
        sensor = common.sensor.Csat3bSensor(log)
        for line in CSAT3B_DATA:
            last_index = line.rfind(",")
            input_line = line[:last_index]
            expected_signature = int(line[last_index + 1 :], 16)
            signature = common.sensor.compute_signature(input_line, sensor.delimiter)
            assert signature == expected_signature

    async def test_hx85ba_dew_point(self) -> None:
        # Test data from
        # doc/Dewpoint_Calculation_Humidity_Sensor_E.pdf
        # RH=10%, T=25°C -> Dew point = -8.77°C
        # RH=90%, T=50°C -> Dew point = 47.90°C
        # List of (data dict for the hx85a topic, expected dew point)
        data_list = [
            (dict(relativeHumidity=10.0, temperature=25.0), -8.77),
            (dict(relativeHumidity=90.0, temperature=50.0), 47.90),
        ]
        # Test the compute_dew_point static method
        for data_dict, desired_dew_point in data_list:
            dew_point = common.sensor.Hx85baSensor.compute_dew_point(
                relative_humidity=data_dict["relativeHumidity"],
                temperature=data_dict["temperature"],
            )
            assert dew_point == pytest.approx(desired_dew_point, abs=0.005)

    def create_wind_sensor_line(
        self,
        sensor: common.sensor.WindsonicSensor,
        speed: str,
        direction: str,
        valid_checksum: bool = True,
    ) -> str:
        """Create a line of output as can be expected from a wind sensor."""
        checksum_string: str = (
            common.sensor.WindsonicSensor.unit_identifier
            + sensor.delimiter
            + direction
            + sensor.delimiter
            + speed
            + sensor.delimiter
            + common.sensor.WindsonicSensor.windspeed_unit
            + sensor.delimiter
            + common.sensor.WindsonicSensor.good_status
            + sensor.delimiter
        )
        checksum = common.sensor.compute_checksum(checksum_string)

        # Mock a bad checksum
        if not valid_checksum:
            checksum = 0

        line = (
            common.sensor.WindsonicSensor.start_character
            + checksum_string
            + common.sensor.WindsonicSensor.end_character
            + f"{checksum:02x}"
            + sensor.terminator
        )
        return line
