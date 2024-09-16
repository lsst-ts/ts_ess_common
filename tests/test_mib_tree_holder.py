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

        enterprises_children = [
            branch
            for branch in mib_tree_holder.mib_tree
            if mib_tree_holder.mib_tree[branch].parent is not None
            and mib_tree_holder.mib_tree[branch].parent.name == "enterprises"
        ]
        assert len(enterprises_children) == 3
        assert "eaton" in enterprises_children
        assert "pdu" in enterprises_children
        assert "schneiderPm5xxx" in enterprises_children

        assert "xups" in mib_tree_holder.mib_tree
        assert mib_tree_holder.mib_tree["xups"].parent.name == "eaton"

        assert len(mib_tree_holder.pending_modules) == 0
