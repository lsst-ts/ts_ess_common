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
import types
import typing
import unittest
from unittest.mock import AsyncMock

import numpy as np
import pytest
from lsst.ts.ess import common


class SiglentSSA3000xDataClientTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_siglent_ssa3000x_spectrum_analyzer_data_client(self) -> None:
        log = logging.getLogger()
        tel_spectrum_analyzer = AsyncMock()
        tel_spectrum_analyzer.set_write = self.set_spectrum
        topics = types.SimpleNamespace(tel_spectrumAnalyzer=tel_spectrum_analyzer)
        config_dict = dict(
            host="localhost",
            port=5000,
            connect_timeout=5,
            read_timeout=1,
            max_read_timeouts=5,
            location="Test Location",
            sensor_name="MockSSA3000X",
            poll_interval=0.1,
            freq_start_value=0.0,
            freq_start_unit="GHz",
            freq_stop_value=3.0,
            freq_stop_unit="GHz",
        )
        self.config = types.SimpleNamespace(**config_dict)

        data_client = common.data_client.SiglentSSA3000xSpectrumAnalyzerDataClient(
            config=self.config,
            topics=topics,
            log=log,
            simulation_mode=1,
        )

        await data_client.start()
        await asyncio.sleep(1.0)

        assert self.start_frequency == pytest.approx(
            common.data_client.SiglentSSA3000xSpectrumAnalyzerDataClient.start_frequency
        )
        assert self.stop_frequency == pytest.approx(
            common.data_client.SiglentSSA3000xSpectrumAnalyzerDataClient.stop_frequency
        )
        assert np.amax(self.spectrum) <= 0.0
        assert np.amin(self.spectrum) >= -100.0

        await data_client.stop()

    async def set_spectrum(self, **kwargs: typing.Any) -> None:
        if "startFrequency" in kwargs:
            self.start_frequency = kwargs["startFrequency"]
        if "stopFrequency" in kwargs:
            self.stop_frequency = kwargs["stopFrequency"]
        if "spectrum" in kwargs:
            self.spectrum = kwargs["spectrum"]
