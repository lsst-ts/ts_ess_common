# This file is part of ts_ess_csc.
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
import math
import types
import typing
import unittest
from unittest.mock import MagicMock

import numpy as np
import pytest
from lsst.ts import utils
from lsst.ts.ess import common
from lsst.ts.ess.common.sensor import compute_dew_point_magnus

# Standard timeout (sec).
STD_TIMEOUT = 5

# Timeout (sec) for creating the controller and remote.
LONG_TIMEOUT = 30


class Young32400DataClientTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        default_config_dict = dict(
            host="localhost",
            connect_timeout=5,
            read_timeout=1,
            max_read_timeouts=5,
            num_samples_airflow=20,
            num_samples_temperature=20,
            rain_stopped_interval=30,
            sensor_name_airflow="05108",
            sensor_name_dew_point="computed",
            sensor_name_humidity="41382VC",
            sensor_name_pressure="61402V",
            sensor_name_rain="52202H",
            sensor_name_temperature="41382VC",
            scale_offset_humidity=[0.025, 0],
            scale_offset_pressure=[48, 500],
            scale_offset_temperature=[0.025, -50],
            scale_offset_wind_direction=[0.1, 0],
            scale_offset_wind_speed=[0.0834, 0],
            scale_rain_rate=0.1,
            location="WeatherStation",
            rate_limit=0,
        )
        self.default_config = types.SimpleNamespace(**default_config_dict)
        self.log = logging.getLogger()

        self.air_flow_event = asyncio.Event()
        self.dew_point_event = asyncio.Event()
        self.precipitation_event = asyncio.Event()
        self.pressure_event = asyncio.Event()
        self.rain_rate_event = asyncio.Event()
        self.relative_humidity_event = asyncio.Event()
        self.temperature_event = asyncio.Event()

    def create_data_client(
        self, config: types.SimpleNamespace
    ) -> common.data_client.Young32400WeatherStationDataClient:
        """Create a Young32400WeatherStationDataClient in simulation mode."""
        self.tel_air_flow = types.SimpleNamespace(
            data=types.SimpleNamespace(
                direction=math.nan,
                directionStdDev=math.nan,
                speed=math.nan,
                speedStdDev=math.nan,
                maxSpeed=math.nan,
            )
        )
        self.tel_air_flow.set = MagicMock()
        self.tel_air_flow.set_write = self.set_air_flow

        self.tel_dew_point = types.SimpleNamespace(
            data=types.SimpleNamespace(dewPointItem=math.nan)
        )
        self.tel_dew_point.set = MagicMock()
        self.tel_dew_point.set_write = self.set_dew_point

        self.tel_pressure = types.SimpleNamespace(
            data=types.SimpleNamespace(
                pressureItem=[math.nan, math.nan, math.nan, math.nan]
            )
        )
        self.tel_pressure.DataType = MagicMock(
            return_value=types.SimpleNamespace(
                pressureItem=[math.nan, math.nan, math.nan, math.nan]
            )
        )
        self.tel_pressure.set = MagicMock()
        self.tel_pressure.set_write = self.set_pressure

        self.tel_rain_rate = types.SimpleNamespace(
            data=types.SimpleNamespace(rainRateItem=math.nan)
        )
        self.tel_rain_rate.set = MagicMock()
        self.tel_rain_rate.set_write = self.set_rain_rate

        self.tel_relative_humidity = types.SimpleNamespace(
            data=types.SimpleNamespace(relativeHumidityItem=math.nan)
        )
        self.tel_relative_humidity.set = MagicMock()
        self.tel_relative_humidity.set_write = self.set_relative_humidity

        self.tel_temperature = types.SimpleNamespace(
            data=types.SimpleNamespace(
                temperatureItem=[math.nan, math.nan, math.nan, math.nan]
            )
        )
        self.tel_temperature.DataType = MagicMock(
            return_value=types.SimpleNamespace(
                temperatureItem=[math.nan, math.nan, math.nan, math.nan]
            )
        )
        self.tel_temperature.set = MagicMock()
        self.tel_temperature.set_write = self.set_temperature

        self.evt_precipitation = types.SimpleNamespace()
        self.evt_precipitation.set = MagicMock()
        self.evt_precipitation.set_write = self.set_precipitation

        self.topics = types.SimpleNamespace(
            tel_airFlow=self.tel_air_flow,
            tel_dewPoint=self.tel_dew_point,
            tel_relativeHumidity=self.tel_relative_humidity,
            tel_pressure=self.tel_pressure,
            tel_rainRate=self.tel_rain_rate,
            tel_temperature=self.tel_temperature,
            evt_precipitation=self.evt_precipitation,
        )

        return common.data_client.Young32400WeatherStationDataClient(
            config=config,
            topics=self.topics,
            log=self.log,
            simulation_mode=True,
        )

    async def set_air_flow(self, **kwargs: typing.Any) -> None:
        self.tel_air_flow.data.direction = kwargs["direction"]
        self.tel_air_flow.data.direction_std_dev = kwargs["directionStdDev"]
        self.tel_air_flow.data.speed = kwargs["speed"]
        self.tel_air_flow.data.speed_std_dev = kwargs["speedStdDev"]
        self.tel_air_flow.data.maxSpeed = kwargs["maxSpeed"]
        self.air_flow_event.set()

    async def set_dew_point(self, **kwargs: typing.Any) -> None:
        self.tel_dew_point.data.dewPointItem = kwargs["dewPointItem"]
        self.dew_point_event.set()

    async def set_precipitation(self, **kwargs: typing.Any) -> None:
        self.precipitation_event.set()

    async def set_pressure(self, **kwargs: typing.Any) -> None:
        self.pressure_event.set()

    async def set_rain_rate(self, **kwargs: typing.Any) -> None:
        self.tel_rain_rate.data.rainRateItem = kwargs["rainRateItem"]
        self.rain_rate_event.set()

    async def set_relative_humidity(self, **kwargs: typing.Any) -> None:
        self.tel_relative_humidity.data.relativeHumidityItem = kwargs[
            "relativeHumidityItem"
        ]
        self.relative_humidity_event.set()

    async def set_temperature(self, **kwargs: typing.Any) -> None:
        self.temperature_event.set()

    async def test_raw_data_generator(self) -> None:
        field_name_index = {
            field_name: i
            for i, field_name in enumerate(
                common.data_client.Young32400RawDataGenerator.stat_names
            )
        }
        config = self.default_config

        # Test some obvious values with zero std deviation
        for field_name, mean, expected_raw in (
            ("wind_direction", 0, "0000"),
            ("wind_direction", 180, "1800"),
            ("wind_direction", 359.9, "3599"),
            ("wind_direction", 360.1, "0001"),
            ("temperature", -50, "0000"),
            ("temperature", 0, "2000"),
            ("temperature", 50, "4000"),
            ("humidity", 0, "0000"),
            ("humidity", 50, "2000"),
            ("humidity", 100, "4000"),
        ):
            data_gen = common.data_client.Young32400RawDataGenerator(
                **{"mean_" + field_name: mean, "std_" + field_name: 0}  # type: ignore
            )
            raw_data = data_gen.create_raw_data_list(config=config, num_items=5)
            field_index = field_name_index[field_name]
            for item in raw_data:
                strings = item.split()
                assert strings[field_index] == expected_raw

        # Test a set of statistics with nonzero std dev.
        num_items = 1000
        data_gen = common.data_client.Young32400RawDataGenerator()
        raw_data = data_gen.create_raw_data_list(config=config, num_items=num_items)
        assert len(raw_data) == num_items
        values = np.array(
            [[float(strval) for strval in item.split()] for item in raw_data],
            dtype=float,
        )
        assert values.shape == (
            num_items,
            len(common.data_client.Young32400RawDataGenerator.stat_names),
        )

        # Compute mean and standard deviation of all raw values.
        # Warning: the values for wind_direction are not trustworthy,
        # due to wraparound and the values for rain_rate are meaningless.
        raw_means = np.mean(values, axis=0)
        raw_stds = np.std(values, axis=0)
        for field_name, field_index in field_name_index.items():
            expected_mean = getattr(data_gen, "mean_" + field_name)
            expected_std = getattr(data_gen, "std_" + field_name)
            if field_name == "rain_rate":
                # The count increments rarely (approx. 20 times over all
                # 1000 samples), so rounding to the nearest int for raw data
                # really messes up the statistics.
                # Just compare the rate derived from final - initial counts
                # to the mean, and be very generous in how close it has to be.
                # We could do better by measuring from the first to the last
                # tip count transition, but this is simpler and good enough.
                tip_counts = values[:, field_index]
                delta_counts = tip_counts[-1] - tip_counts[0]
                if delta_counts < 0:
                    delta_counts += (
                        common.data_client.Young32400RawDataGenerator.max_rain_tip_count
                    )
                samples_per_hour = 60 * 50 / data_gen.read_interval
                mm_per_count = config.scale_rain_rate
                mean = (delta_counts / num_items) * mm_per_count * samples_per_hour
                print(f"{field_name=}; {mean=:0.2f}; {expected_mean=}; {expected_std=}")
                assert mean == pytest.approx(expected_mean, abs=expected_std * 2)
            elif field_name == "wind_direction":
                # Use circular statistics.
                scale, offset = config.scale_offset_wind_direction
                wind_direction_deg = values[:, field_index] * scale + offset
                mean, std = common.accumulator.get_circular_mean_and_std_dev(
                    wind_direction_deg
                )
                mean_diff = utils.angle_diff(mean, expected_mean).deg
                # Be generous in these comparisons; this is a sanity check
                # that should pass for essentially all random seeds.
                print(
                    f"{field_name=}; {mean=:0.2f}; {expected_mean=}; {std=:0.2f}; {expected_std=}"
                )
                assert mean_diff == pytest.approx(0, abs=expected_std)
                assert std == pytest.approx(expected_std, rel=0.1)
            else:
                # Use standard statistics.
                scale, offset = getattr(config, "scale_offset_" + field_name)
                mean = raw_means[field_index] * scale + offset
                std = raw_stds[field_index] * scale
                # Be generous in these comparisons; this is a sanity check
                # that should pass for essentially all random seeds.
                print(
                    f"{field_name=}; {mean=:0.2f}; {expected_mean=}; {std=:0.2f}; {expected_std=}"
                )
                assert mean == pytest.approx(expected_mean, abs=expected_std)
                assert std == pytest.approx(expected_std, rel=0.1)

    async def test_operation(self) -> None:
        config = self.default_config
        config.rain_stopped_interval = 2  # very short
        data_client = self.create_data_client(config)

        # Make the test run quickly
        read_interval = 0.1
        data_client.simulation_interval = read_interval

        # Use an unrealistically large rain rate (50 mm/hr is heavy),
        # so we don't have to wait as long to get rain reported.
        data_gen = common.data_client.Young32400RawDataGenerator(
            read_interval=read_interval,
            mean_rain_rate=360,  # about 1 tip/second
        )
        num_checks_per_topic = 2
        # Need enough items to report rain rate num_checks_per_topic times,
        # plus margin.
        num_items = int(
            (num_checks_per_topic + 1) * config.rain_stopped_interval / read_interval
        )
        data_client.simulated_raw_data = data_gen.create_raw_data_list(
            config=config, num_items=num_items
        )
        await data_client.start()
        # await asyncio.sleep(10)

        try:
            for i in range(num_checks_per_topic):
                await self.check_air_flow(config=config, data_gen=data_gen)
                await self.check_humidity_temperature_pressure_dew_point(
                    config=config, data_gen=data_gen
                )
                if i == 0:
                    await self.precipitation_event.wait()
                    assert self.tel_rain_rate.data.rainRateItem
                await self.check_rain_rate(config=config, data_gen=data_gen)

            # When the simulator runs out of simulated data,
            # this gives the rain stopped timer a chance to expire.
            # data = await self.remote.evt_precipitation.next(
            #     flush=False, timeout=STD_TIMEOUT
            # )
            # assert not data.raining
        finally:
            await data_client.stop()

    async def check_air_flow(
        self,
        config: types.SimpleNamespace,
        data_gen: common.data_client.Young32400RawDataGenerator,
    ) -> None:
        """Check the next sample of airFlow.

        Parameters
        ----------
        config : `types.SimpleNamespace`
            The configuration of the weather data client.
        data_gen : `common.data_client.Young32400RawDataGenerator`
            The data generator used to generate simulated raw data.
        """
        await self.air_flow_event.wait()

        direction_diff = utils.angle_diff(
            self.tel_air_flow.data.direction, data_gen.mean_wind_direction
        ).deg
        assert direction_diff == pytest.approx(0, abs=data_gen.std_wind_direction)

        # Note: the standard deviation is computed from a small number
        # of samples and direction is cast to int (in ts_xml 15)
        # so it may vary even more from the specified value.
        assert self.tel_air_flow.data.direction_std_dev == pytest.approx(
            data_gen.std_wind_direction, rel=1
        )
        assert self.tel_air_flow.data.speed == pytest.approx(
            data_gen.mean_wind_speed, rel=data_gen.std_wind_speed
        )
        assert self.tel_air_flow.data.speed_std_dev == pytest.approx(
            data_gen.std_wind_speed, rel=0.5
        )

    async def check_humidity_temperature_pressure_dew_point(
        self,
        config: types.SimpleNamespace,
        data_gen: common.data_client.Young32400RawDataGenerator,
    ) -> None:
        """Check the next sample of relativeHumidity, temperature,
        pressure and dewPoint.

        Parameters
        ----------
        config : `types.SimpleNamespace`
            The configuration of the weather data client.
        data_gen : `common.data_client.Young32400RawDataGenerator`
            The data generator used to generate simulated raw data.
        """
        await self.relative_humidity_event.wait()
        data = self.tel_relative_humidity.data
        read_humidity = data.relativeHumidityItem
        assert data.relativeHumidityItem == pytest.approx(
            data_gen.mean_humidity, abs=data_gen.std_humidity
        )

        await self.temperature_event.wait()
        data = self.tel_temperature.data
        read_temperature = data.temperatureItem[0]
        assert read_temperature == pytest.approx(
            data_gen.mean_temperature, abs=data_gen.std_temperature
        )
        assert all(math.isnan(value) for value in data.temperatureItem[1:])

        await self.pressure_event.wait()
        data = self.tel_pressure.data
        assert data.pressureItem[0] == pytest.approx(
            data_gen.mean_pressure, abs=data_gen.std_pressure
        )
        assert all(math.isnan(value) for value in data.pressureItem[1:])

        expected_dew_point = compute_dew_point_magnus(
            relative_humidity=read_humidity,
            temperature=read_temperature,
        )
        await self.dew_point_event.wait()
        data = self.tel_dew_point.data
        assert data.dewPointItem == pytest.approx(expected_dew_point)

    async def check_rain_rate(
        self,
        config: types.SimpleNamespace,
        data_gen: common.data_client.Young32400RawDataGenerator,
    ) -> None:
        """Check the next sample of rainRate.

        Parameters
        ----------
        config : `types.SimpleNamespace`
            The configuration of the weather data client.
        data_gen : `common.data_client.Young32400RawDataGenerator`
            The data generator used to generate simulated raw data.
        """
        await self.rain_rate_event.wait()
        data = self.tel_rain_rate.data
        assert data.rainRateItem == pytest.approx(data_gen.mean_rain_rate, rel=0.1)
