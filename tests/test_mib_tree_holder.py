# This file is part of ts_ess_common.
#
# Developed for the Vera Rubin Observatory Telescope and Site Systems.
# This product includes software developed by the Vera Rubin Observatory
# Project (https://www.lsst.org).
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

import unittest

from lsst.ts.ess import common


class MibTreeTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_mib_tree(self) -> None:
        mib_tree_holder = common.MibTreeHolder()
        assert str(mib_tree_holder.mib_tree["sysDescr"]) == "1.3.6.1.2.1.1.1"
        assert mib_tree_holder.mib_tree["sysDescr"].oid == "1.3.6.1.2.1.1.1"

        enterprises_children = sorted(
            {
                branch
                for branch in mib_tree_holder.mib_tree
                if mib_tree_holder.mib_tree[branch].parent is not None
                and mib_tree_holder.mib_tree[branch].parent.name == "enterprises"
            }
        )
        assert len(enterprises_children) == 4
        assert common.DeviceName.schneiderPm5xxx.value == enterprises_children.pop()
        assert common.DeviceName.raritan.value == enterprises_children.pop()
        assert common.DeviceName.netbooter.value == enterprises_children.pop()
        assert "eaton" == enterprises_children.pop()
        assert len(enterprises_children) == 0

        assert common.DeviceName.xups.value in mib_tree_holder.mib_tree
        assert (
            mib_tree_holder.mib_tree[common.DeviceName.xups.value].parent.name
            == "eaton"
        )

        assert len(mib_tree_holder.pending_modules) == 0
