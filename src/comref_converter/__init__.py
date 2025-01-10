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
Load the comref_converter package properly.
"""

__version__ = "0.8.1"
__author__ = "Pau Torras"

from .mtn import ast as AST
from .translator_base import MeasureID
from .translator_mei import TranslatorMEI
from .translator_mxml import TranslatorMXML
from .translator_sequence import TranslatorSequence
from .translator_xml import TranslatorXML
from .visitor_count_nodes import VisitorCountNodes
from .visitor_get_nodes import VisitorGetNodes
from .visitor_to_abaro import VisitorToABaro
from .visitor_to_apted import VisitorToAPTED
from .visitor_to_dot import VisitorToDOT
from .visitor_to_mei import VisitorToMEI
from .visitor_to_mxml import VisitorToMXML
from .visitor_to_sequence import VisitorToModelSequence
from .visitor_to_xml import VisitorToXML

translators = [
    TranslatorMEI,
    TranslatorMXML,
    TranslatorSequence,
    TranslatorXML,
]
visitors = [
    VisitorCountNodes,
    VisitorToAPTED,
    VisitorToDOT,
    VisitorToMEI,
    VisitorToModelSequence,
    VisitorToMXML,
    VisitorToXML,
    VisitorToABaro,
]
