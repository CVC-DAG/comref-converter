"""The Common Optical Music Recognition Framework (COMReF) toolset.

APTED tree data structure.

Copyright (C) 2023, Pau Torras <ptorras@cvc.uab.cat>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from __future__ import annotations

from typing import Optional

from apted.helpers import Tree


class AptedTree(Tree):
    def __init__(self, name, *children):
        super().__init__(name, *children)
        self.note_id: Optional[int] = None

    @classmethod
    def from_text(cls, text):
        return super().from_text(text)

    @classmethod
    def decorate_tree_with_note_ids(cls, tree: AptedTree) -> None:
        note_id = 0

        def __navigate(tree: AptedTree) -> None:
            nonlocal note_id
            if tree.name in {"note", "rest"}:
                tree.note_id = note_id
                note_id += 1
                return None
            for nd in tree.children:
                __navigate(nd)

        __navigate(tree)
