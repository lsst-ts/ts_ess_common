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

__all__ = ["MibTreeHolder"]

import logging
import pathlib
import re
import typing

from .utils import MibTreeElement, MibTreeElementType

# SNMP-related constants.
MODULE_IDENTITY = r"^(\w+) +MODULE-IDENTITY$"
OBJECT_IDENTIFIER = r"^(\w+) +OBJECT IDENTIFIER +::= \{ ?(\w+) +(\d+) ?\}$"
OBJECT_TYPE = r"^(\w+) OBJECT-TYPE$"
MIB_OID = r"^::= ?{ ?(\w+) +(\d+) ? ?}$"
DESCRIPTION = "DESCRIPTION"
INDEX = r"INDEX +\{ ?([\w, ]+) ?\}"

DATA_DIR = pathlib.Path(__file__).parent / "data"


class MibTreeHolder:
    """Holder of information in an MIB tree.

    MIB stands for Management Information Base and holds the information for
    managing the entities in a communication network, in this case SNMP or
    Simple Network Management Protocol. The information can be represented as a
    tree, hence the name of the class.
    """

    def __init__(self) -> None:
        self.log = logging.getLogger(type(self).__name__)
        self._line_num = 0
        self.mib_tree: dict[str, MibTreeElement] = {}

        # In some cases a module is defined before its parent. In such cases
        # this is used to keep track of modules that need to be added as soon
        # as the parent is added.
        self.pending_modules: dict[str, typing.Tuple[str, str]] = {}

        self._add_default_elements()
        self._add_mib_elements()

    def _add_default_elements(self) -> None:
        """Add the default MIB elements.

        The default elements are the root, system and enterprises branches as
        well as a branch for Eaton PDU devices since their MIB file has a
        deviating syntax."""
        snmp = MibTreeElement(
            name="snmp",
            description="snmp",
            oid="1.3.6.1",
            parent=None,
            type=MibTreeElementType.BRANCH,
        )
        system = MibTreeElement(
            name="system",
            description="system",
            oid="1.3.6.1.2",
            parent=snmp,
            type=MibTreeElementType.BRANCH,
        )
        sys_descr = MibTreeElement(
            name="sysDescr",
            description="System Description.",
            oid="1.3.6.1.2.1.1.1",
            parent=system,
            type=MibTreeElementType.BRANCH,
        )
        private = MibTreeElement(
            name="private",
            description="private",
            oid="1.3.6.1.4",
            parent=snmp,
            type=MibTreeElementType.BRANCH,
        )
        enterprises = MibTreeElement(
            name="enterprises",
            description="enterprises",
            oid="1.3.6.1.4.1",
            parent=private,
            type=MibTreeElementType.BRANCH,
        )
        self.mib_tree[snmp.name] = snmp
        self.mib_tree[system.name] = system
        self.mib_tree[sys_descr.name] = sys_descr
        self.mib_tree[private.name] = private
        self.mib_tree[enterprises.name] = enterprises

    def _add_mib_elements(self) -> None:
        """Loop over the MIB files and add their contents as a tree
        structure."""
        for filename in sorted(DATA_DIR.glob("*.mib")):
            self.log.debug(f"Processing {filename}.")
            with open(filename) as f:
                lines = f.readlines()

            for self._line_num in range(len(lines)):
                line = lines[self._line_num].strip()
                mod_id_match = re.match(MODULE_IDENTITY, line)
                obj_id_match = re.match(OBJECT_IDENTIFIER, line)
                obj_type_match = re.match(OBJECT_TYPE, line)
                if mod_id_match:
                    self._process_mod_id(lines, line, mod_id_match)
                elif obj_id_match:
                    self._process_obj_id(obj_id_match)
                elif obj_type_match:
                    self._process_obj_type(lines, line, obj_type_match)

    def _process_mod_id(
        self, lines: list[str], line: str, mod_id_match: re.Match
    ) -> None:
        """Utility method to process MODULE-IDENTITY entries.

        If the parent exists the module gets added as a branch. If the parent
        doesn't exist (yet), it will be added to the dict of pending modules so
        it can be added as soon as the parent is added.

        Parameters
        ----------
        lines : `list`[`str`]
            The lines as read from an MIB file.
        line : `str`
            The current line that is processed.
        mod_id_match : `re.Match`
            Regex Match object used to look up the name of the module.
        """
        name = self._get_name_replacement(mod_id_match.group(1))
        mib_oid_match = re.match(MIB_OID, line)
        while not mib_oid_match:
            self._line_num += 1
            line = lines[self._line_num].strip()
            mib_oid_match = re.match(MIB_OID, line)
        parent_name = self._get_name_replacement(mib_oid_match.group(1))
        oid = mib_oid_match.group(2)
        parent = self._get_parent(parent_name)
        if parent is not None:
            self.mib_tree[name] = MibTreeElement(
                name=name,
                description=name,
                oid=f"{parent.oid}.{oid}",
                parent=parent,
                type=MibTreeElementType.BRANCH,
            )
        else:
            self.pending_modules[parent_name] = (name, oid)

    def _process_obj_id(self, obj_id_match: re.Match) -> None:
        """Utility method to process OBJECT IDENTIFIER entries.

        If there is a pending MODULE-IDENTITY entry, that declares this OBJECT
        IDENTIFIER entry as parent, the MODULE-IDENTITY entry gets added as a
        branch as well.

        Parameters
        ----------
        lines : `list`[`str`]
            The lines as read from an MIB file.
        line : `str`
            The current line that is processed.
        mod_id_match : `re.Match`
            Regex Match object used to look up the name of the module.
        """
        name = self._get_name_replacement(obj_id_match.group(1))
        parent_name = obj_id_match.group(2)
        parent = self._get_parent(parent_name)
        assert parent is not None, f"No parent found for {name=!r}"
        self.mib_tree[name] = MibTreeElement(
            name=name,
            description=name,
            oid=f"{parent.oid}.{obj_id_match.group(3)}",
            parent=parent,
            type=MibTreeElementType.BRANCH,
        )
        if name in self.pending_modules:
            branch_name, oid = self.pending_modules[name]
            parent = self._get_parent(name)
            assert parent is not None
            self.mib_tree[branch_name] = MibTreeElement(
                name=branch_name,
                description=branch_name,
                oid=f"{parent.oid}.{oid}",
                parent=parent,
                type=MibTreeElementType.BRANCH,
            )
            self.pending_modules.pop(name)

    def _get_parent(self, parent_name: str) -> MibTreeElement | None:
        """Get the MIB parent branch for the fiven parent name.

        Parameters
        ----------
        parent_name : `str`
            The name of the parent to get.
        """
        parent: MibTreeElement | None = None
        parent_name = self._get_name_replacement(parent_name)
        if parent_name in self.mib_tree:
            parent = self.mib_tree[parent_name]
        return parent

    def _get_name_replacement(self, name: str) -> str:
        """Replace the name if necessary.

        In some cases the name gets replaced by a more generic one. If the name
        is not replaced, it gets returned unmodified.

        Parameters
        ----------
        name : `str`
            The name to replace, or the unmodified name.

        Returns
        -------
        str
            The name replacement.
        """
        name_replacement = name
        if name == "schneiderElectric":
            name_replacement = "schneiderPm5xxx"
        elif name == "synaccess":
            name_replacement = "pdu"
        elif name == "xupsMIB":
            name_replacement = "xups"
        return name_replacement

    def _process_obj_type(
        self, lines: list[str], line: str, obj_type_match: re.Match
    ) -> None:
        """Utility method to process OBJECT_TYPE entries.

        Parameters
        ----------
        lines : `list`[`str`]
            The lines as read from an MIB file.
        line : `str`
            The current line that is processed.
        obj_type_match : `re.Match`
            Regex Match object used to look up the name of the object type.
        """
        name = obj_type_match.group(1)

        description = ""
        while DESCRIPTION not in line:
            self._line_num += 1
            line = lines[self._line_num].strip()
        while "::=" not in line and "INDEX " not in line:
            description += line.replace(DESCRIPTION, "").strip()
            if description != "":
                description += " "
            self._line_num += 1
            line = lines[self._line_num].strip()
        # Remove multiple spaces and strip white space.
        description = re.sub(r" +", " ", description).replace('"', "").strip()

        index: str | None = None
        if "INDEX " in line:
            index_match = re.match(INDEX, line)
            if index_match:
                index = index_match.group(1)
                self._line_num += 1
                line = lines[self._line_num].strip()

        oid_match = re.match(MIB_OID, line)
        assert oid_match is not None
        parent_name = oid_match.group(1)
        parent = self.mib_tree[parent_name]
        oid = oid_match.group(2)

        self.mib_tree[name] = MibTreeElement(
            name=name,
            description=description,
            oid=f"{parent.oid}.{oid}",
            parent=parent,
            type=MibTreeElementType.LEAF,
            index=index,
        )
