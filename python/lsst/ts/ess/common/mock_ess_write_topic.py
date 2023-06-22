from __future__ import annotations

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

__all__ = ["make_mock_ess_topics", "MockEssWriteTopic"]

import collections
import contextlib
import types
import typing
from collections.abc import AsyncGenerator

from lsst.ts import salobj, utils

if typing.TYPE_CHECKING:
    from ..sal_info import SalInfo


@contextlib.asynccontextmanager
async def make_mock_ess_topics(
    *attr_names: str, index: int = 1
) -> AsyncGenerator[types.SimpleNamespace, None]:
    """Make a struct of mock ESS write topics for unit testing data clients.

    Parameters
    ----------
    *attr_names : `list` [`str`]
        List of topic attribute names, e.g.
        ["tel_temperature", "evt_lightningStrike"]
    index : `int`
        The SAL index. Irrelevant unless you want to check the salIndex
        field of the data.
    """
    if not attr_names:
        raise ValueError("You must provide one or more topic attr_names")

    # Use an arbitrary topic subname and index; neither matters
    # because the data is not written to SAL.
    with utils.modify_environ(LSST_TOPIC_SUBNAME="test"):
        async with salobj.Domain() as domain, salobj.SalInfo(
            domain=domain, name="ESS", index=index
        ) as salinfo:
            topics_dict = {
                attr_name: MockEssWriteTopic(salinfo=salinfo, attr_name=attr_name)
                for attr_name in attr_names
            }
            print(f"{topics_dict=}")
            yield types.SimpleNamespace(**topics_dict)


class MockEssWriteTopic(salobj.topics.WriteTopic):
    r"""A version of lsst.ts.salobj.topics.WriteTopic that records
    every message written, instead of writing it to SAL.

    Specific to ESS topics because it assumes that data has a sensorName field.

    This is only intended for unit tests and related short-term use.
    Long-term use will be a memory leak!

    Parameters
    ----------
    salinfo : `SalInfo`
        SAL component information
    attr_name : `str`
        Topic name with attribute prefix. The prefix must be one of:
        ``cmd_``, ``evt_``, ``tel_``, or (only for the ackcmd topic) ``ack_``.
    min_seq_num : `int` or `None`, optional
        Minimum value for the ``private_seqNum`` field. The default is 1.
        If `None` then ``private_seqNum`` is not set; this is needed
        for the ackcmd writer, which sets the field itself.
    max_seq_num : `int`, optional
        Maximum value for ``private_seqNum``, inclusive.
        The default is the maximum allowed positive value
        (``private_seqNum`` is a 4-byte signed int).
        Ignored if ``min_seq_num`` is `None`.
    initial_seq_num : `int`, optional
        Initial sequence number; if `None` use min_seq_num.

    Attributes
    ----------
    data_dict : `list` [`salobj.BaseMsgType`]
        Dict of sensorName: list of data written for that sensor name,
        with newer data at the end of each list.
    Plus the attributes of:
       `WriteTopic`
    """

    def __init__(
        self,
        *,
        salinfo: SalInfo,
        attr_name: str,
        min_seq_num: int | None = 1,
        max_seq_num: int = salobj.topics.MAX_SEQ_NUM,
        initial_seq_num: int | None = None,
    ) -> None:
        super().__init__(
            salinfo=salinfo,
            attr_name=attr_name,
            min_seq_num=min_seq_num,
            max_seq_num=max_seq_num,
            initial_seq_num=initial_seq_num,
        )
        self.data_dict: dict[str, list[salobj.BaseMsgType]] = collections.defaultdict(
            list
        )

    async def write(self) -> salobj.BaseMsgType:
        """Write the current data and return a copy of the data written.

        Returns
        -------
        data : self.DataType
            The data that was written.
            This can be useful to avoid race conditions
            (as found in RemoteCommand).

        Raises
        ------
        RuntimeError
            If not running.
        """
        data = self._prepare_data_to_write()
        self.data_dict[self.data.sensorName].append(data)
        return data
