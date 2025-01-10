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
Load MTN file.
"""


import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from ..mtn import AST
from ..translator_xml import TranslatorXML


class MTNLoader:
    def __init__(self) -> None:
        self.translator = TranslatorXML()

    def load(self, path: Path, first_line: Optional[Path] = None) -> AST.Score:
        root = ET.parse(path)
        score = self.translator(root.getroot())
        self.translator.reset()

        return score
