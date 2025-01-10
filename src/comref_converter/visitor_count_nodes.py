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
A visitor that can count all nodes in a tree.
"""

from .mtn import ast as AST


class VisitorCountNodes(AST.Visitor):
    """Implements conversion to MXML."""

    def visit_ast(self, root: AST.SyntaxNode) -> int:
        """Perform conversion of an MTN tree into XML.

        Parameters
        ----------
        root: AST.SyntaxNode
            Any subtree to convert to XML MTN.

        Returns
        -------
        Dict
            ElementTree Root node containing the entire document converted to XML.
        """
        return root.accept(self)

    def visit_score(self, score: AST.Score) -> int:
        """Perform visiting operation on Score node."""
        return 1 + sum(x.accept(self) for x in score.measures)

    def visit_note(self, note: AST.Note) -> int:
        """Perform visiting operation on Note node."""
        # Notehead node + Note node
        return 2 + len(note.dots) + len(note.accidentals) + len(note.modifiers)

    def visit_toplevel(self, toplevel: AST.TopLevel) -> int:
        """Perform visiting operation on TopLevel node."""
        raise NotImplementedError()

    def visit_token(self, token: AST.Token) -> int:
        """Perform visiting operation on Token node."""
        return 1

    def visit_chord(self, chord: AST.Chord) -> int:
        """Perform visiting operation on Chord node."""
        return (
            1
            + (1 if chord.stem is not None else 0)
            + sum(x.accept(self) for x in chord.notes)
        )

    def visit_rest(self, rest: AST.Rest) -> int:
        """Perform visiting operation on Rest node."""
        # Rest node + rest token
        return 2 + len(rest.dots) + len(rest.modifiers)

    def visit_note_group(self, note_group: AST.NoteGroup) -> int:
        """Perform visiting operation on NoteGroup node."""
        return (
            1
            + sum(x.accept(self) for x in note_group.children)
            + len(note_group.appendages)
        )

    def visit_attributes(self, attributes: AST.Attributes) -> int:
        """Perform visiting operation on Attributes node."""
        subnodes_key = sum(
            x.accept(self) for x in attributes.key.values() if x is not None
        )
        subnodes_clef = sum(
            x.accept(self) for x in attributes.clef.values() if x is not None
        )
        subnodes_timesig = sum(
            x.accept(self) for x in attributes.timesig.values() if x is not None
        )
        return 1 + subnodes_clef + subnodes_key + subnodes_timesig

    def visit_time_signature(self, time_signature: AST.TimeSignature) -> int:
        """Perform visiting operation on TimeSignature node."""
        return (
            1
            + (1 if time_signature.time_symbol is not None else 0)
            + (
                sum(x.accept(self) for x in time_signature.compound_time_signature)
                if time_signature.compound_time_signature is not None
                else 0
            )
        )

    def visit_key(self, key: AST.Key) -> int:
        """Perform visiting operation on Key node."""
        return 1 + len(key.naturals) + len(key.accidentals)

    def visit_clef(self, clef: AST.Clef) -> int:
        """Perform visiting operation on Clef node."""
        return 1 + (1 if clef.clef_token is not None else 0)

    def visit_direction(self, direction: AST.Direction) -> int:
        """Perform visiting operation on Direction node."""
        return 1 + len(direction.directives)

    def visit_measure(self, measure: AST.Measure) -> int:
        """Perform visiting operation on Measure node."""
        return (
            1
            + sum(x.accept(self) for x in measure.elements)
            + (
                measure.left_barline.accept(self)
                if measure.left_barline is not None
                else 0
            )
            + (
                measure.right_barline.accept(self)
                if measure.right_barline is not None
                else 0
            )
        )

    def visit_barline(self, barline: AST.Barline) -> int:
        """Perform visiting operation on Barline node."""
        return 1 + len(barline.barline_tokens) + len(barline.modifiers)

    def visit_tuplet(self, tuplet: AST.Tuplet) -> int:
        """Perform visiting operation on Tuplet node."""
        return 1 + (tuplet.number.accept(self) if tuplet.number is not None else 0) + 1

    def visit_numerator(self, numerator: AST.Numerator) -> int:
        """Perform visiting operation on Numerator node."""
        return 1 + sum(x.accept(self) for x in numerator.digits_or_sum)

    def visit_denominator(self, denominator: AST.Denominator) -> int:
        """Perform visiting operation on Denominator node."""
        return 1 + denominator.digits.accept(self)

    def visit_number(self, number: AST.Number) -> int:
        """Perform visiting operation on Number node."""
        return 1 + len(number.digits)

    def visit_timesig_fraction(self, fraction: AST.TimesigFraction) -> int:
        """Perform visiting operation on timesig fraction node."""
        return (
            1
            + fraction.numerator.accept(self)
            + (
                fraction.denominator.accept(self)
                if fraction.denominator is not None
                else 0
            )
        )
