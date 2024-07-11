"""The Common Optical Music Recognition Framework (COMReF) toolset.

Convert MTN AST into MEI.

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


# TODO: Since the system only supports measure-level annotations, the scope for MEI
# conversion is limited. Thus, propagating semantics and joining measures would be
# needed.

# TODO: This has to be implemented.


import xml.etree.ElementTree as ET

from .mtn import ast as AST


class VisitorToMEI(AST.Visitor):
    """Implements conversion to MEI."""

    def __init__(self) -> None:
        super().__init__()

    def visit_ast(self, root: AST.SyntaxNode) -> ET.ElementTree:
        """Perform conversion of an MTN tree into MEI.

        Parameters
        ----------
        root: AST.SyntaxNode
            Any subtree to convert to MEI.

        Returns
        -------
        Dict
            ElementTree Root node containing the entire document converted to XML.
        """
        return root.accept(self)

    def visit_note(self, note: AST.Note) -> ET.Element:
        """Perform visiting operation on Note node."""
        raise NotImplementedError()

    def visit_toplevel(self, toplevel: AST.TopLevel) -> ET.Element:
        """Perform visiting operation on TopLevel node."""
        raise NotImplementedError()

    def visit_token(self, token: AST.Token) -> ET.Element:
        """Perform visiting operation on Token node."""
        raise NotImplementedError()

    def visit_chord(self, chord: AST.Chord) -> ET.Element:
        """Perform visiting operation on Chord node."""
        raise NotImplementedError()

    def visit_rest(self, rest: AST.Rest) -> ET.Element:
        """Perform visiting operation on Rest node."""
        raise NotImplementedError()

    def visit_note_group(self, note_group: AST.NoteGroup) -> ET.Element:
        """Perform visiting operation on NoteGroup node."""
        raise NotImplementedError()

    def visit_attributes(self, attributes: AST.Attributes) -> ET.Element:
        """Perform visiting operation on Attributes node."""
        raise NotImplementedError()

    def visit_time_signature(self, time_signature: AST.TimeSignature) -> ET.Element:
        """Perform visiting operation on TimeSignature node."""
        raise NotImplementedError()

    def visit_key(self, key: AST.Key) -> ET.Element:
        """Perform visiting operation on Key node."""
        raise NotImplementedError()

    def visit_clef(self, clef: AST.Clef) -> ET.Element:
        """Perform visiting operation on Clef node."""
        raise NotImplementedError()

    def visit_direction(self, direction: AST.Direction) -> ET.Element:
        """Perform visiting operation on Direction node."""
        raise NotImplementedError()

    def visit_measure(self, measure: AST.Measure) -> ET.Element:
        """Perform visiting operation on Measure node."""
        raise NotImplementedError()

    def visit_barline(self, barline: AST.Barline) -> ET.Element:
        """Perform visiting operation on Barline node."""
        raise NotImplementedError()

    def visit_tuplet(self, tuplet: AST.Tuplet) -> ET.Element:
        """Perform visiting operation on Tuplet node."""
        raise NotImplementedError()

    def visit_numerator(self, numerator: AST.Numerator) -> ET.Element:
        """Perform visiting operation on Numerator node."""
        raise NotImplementedError()

    def visit_denominator(self, denominator: AST.Denominator) -> ET.Element:
        """Perform visiting operation on Denominator node."""
        raise NotImplementedError()

    def visit_number(self, number: AST.Number) -> ET.Element:
        """Perform visiting operation on Number node."""
        raise NotImplementedError()

    def visit_timesig_fraction(self, fraction: AST.TimesigFraction) -> ET.Element:
        """Perform visiting operation on timesig fraction node."""
        raise NotImplementedError()
