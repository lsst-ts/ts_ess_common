# This file is part of ts_salobj.
#
# Developed for the Rubin Observatory Telescope and Site System.
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

import collections
import typing
import unittest

import numpy as np
from lsst.ts.ess import common

# Long enough to perform any reasonable operation
# including starting a CSC or loading a script (seconds)
STD_TIMEOUT = 10
# Time for events to be output as a result of a command (seconds).
EVENT_DELAY = 0.1
# Timeout for when we expect no new data (seconds)
NO_DATA_TIMEOUT = 1

np.random.seed(47)


class TopicsTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_mock_write_topic(self) -> None:
        # Test a range of topics: a scalar-valued telemetry topic,
        # an array-valued telemetry-topic, and an event.
        topic_attr_names = (
            "tel_relativeHumidity",
            "tel_temperature",
            "evt_lightningStrike",
        )
        async with common.make_mock_ess_topics(*topic_attr_names) as topics:
            for attr_name in topic_attr_names:
                assert hasattr(topics, attr_name)

            num_temperatures = len(topics.tel_temperature.DataType().temperature)

            # Create the test_data first, then iterate over it,
            # to make mypy happier.
            sensor_names = ("big", "big", "little")
            test_data: list[tuple[str, list[dict[str, typing.Any]]]] = [
                (
                    "tel_relativeHumidity",
                    [
                        dict(relativeHumidity=val, sensorName=sensor_name)
                        for val, sensor_name in zip((20.2, 30.3, 40.4), sensor_names)
                    ],
                ),
                (
                    "tel_temperature",
                    [
                        dict(
                            temperature=[val] * num_temperatures,
                            numChannels=5,
                            sensorName=sensor_name,
                        )
                        for val, sensor_name in zip((1.1, 2.2, 3.3), sensor_names)
                    ],
                ),
                (
                    "evt_lightningStrike",
                    [
                        dict(correctedDistance=val, sensorName=sensor_name)
                        for val, sensor_name in zip((44.4, 55.5, 66.6), sensor_names)
                    ],
                ),
            ]
            for attr_name, data_list in test_data:
                topic = getattr(topics, attr_name)
                expected_len_by_sensor_name: dict[str, int] = collections.defaultdict(
                    int
                )
                assert (
                    topic.default_force_output is False
                    if attr_name.startswith("evt")
                    else True
                )
                assert len(topic.data_dict) == 0

                for data in data_list:
                    sensor_name = data["sensorName"]
                    expected_len_by_sensor_name[sensor_name] += 1
                    result = await topic.set_write(**data)
                    assert result.did_change
                    assert result.was_written
                    assert (
                        len(topic.data_dict[sensor_name])
                        == expected_len_by_sensor_name[sensor_name]
                    )
                    for key, value in data.items():
                        assert getattr(topic.data_dict[sensor_name][-1], key) == value
                        assert getattr(result.data, key) == value

                # Write the last data again. This should only write and add
                # data if the topic is not an event.
                result = await topic.set_write(**data)
                assert not result.did_change
                assert result.was_written == topic.default_force_output
                if result.was_written:
                    assert (
                        len(topic.data_dict[sensor_name])
                        == expected_len_by_sensor_name[sensor_name] + 1
                    )
                else:
                    assert (
                        len(topic.data_dict[sensor_name])
                        == expected_len_by_sensor_name[sensor_name]
                    )
