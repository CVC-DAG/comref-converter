# The CWMN Optical Music Recognition Framework (COMREF) toolset.
#
# Copyright (C) 2023, Pau Torras <ptorras@cvc.uab.cat>
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
"""
Helper class to manage a stack of NoteGroups.
"""


from typing import Dict, List, Optional

from . import mtn as MTN
from .music_state import ScoreState
from .symbol_table import SymbolTable


class GroupStack:
    def __init__(self, score_state: ScoreState, symbol_table: SymbolTable) -> None:
        self.score_state = score_state
        self.symbol_table = symbol_table

        self.stack: Dict[bool, List[MTN.AST.NoteGroup]] = {
            grace: [] for grace in [False, True]
        }

    def new_level(self, grace: bool) -> MTN.AST.NoteGroup:
        """Create a new beaming level."""
        new_group = MTN.AST.NoteGroup(
            self.score_state.current_time,
            [],
            [
                MTN.AST.Token(
                    MTN.TT.TokenType.BEAM,
                    {},
                    MTN.MS.StaffPosition(None, None),
                    self.symbol_table.give_identifier(),
                )
            ],
        )
        self.push(grace, new_group)
        return new_group

    def push(self, grace: bool, group: MTN.AST.NoteGroup) -> None:
        """Add new element to the stack."""
        if len(self.stack[grace]) > 0:
            self.stack[grace][-1].children.append(group)
        self.stack[grace].append(group)

    def pop(self, grace: bool) -> Optional[MTN.AST.NoteGroup]:
        """Remove element from the stack."""
        if len(self.stack[grace]) == 0:
            raise ValueError("No NoteGroup is present in the stack")

        return self.stack[grace].pop()

    def top(self, grace: bool) -> Optional[MTN.AST.NoteGroup]:
        """Return the element at the top of the stack if it exists."""
        if len(self.stack[grace]) == 0:
            return None
        return self.stack[grace][-1]

    def bottom(self, grace: bool) -> Optional[MTN.AST.NoteGroup]:
        """Return the element at the bottom of the stack if it exists."""
        if len(self.stack[grace]) == 0:
            return None
        return self.stack[grace][0]

    def length(self, grace: bool) -> int:
        """Get number of elements in the stack."""
        return len(self.stack[grace])

    def reset(self) -> None:
        """Set back to default empty state."""
        self.stack = {grace: [] for grace in [False, True]}

    def reset_grace(self, grace: bool) -> None:
        """Set back to default empty state only for the given grace note."""
        self.stack[grace] = []
