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
An iterator over all Note objects in the tree in MTN order.
"""


from typing import Sequence, Union

from .mtn import ast as AST


class VisitorGetNotes(AST.Visitor):
    """Get all note and rest nodes in the tree."""

    def visit_ast(self, root: AST.SyntaxNode) -> Sequence[Union[AST.Note, AST.Rest]]:
        """Perform visiting operation."""
        return root.accept(self)

    def visit_score(self, score: AST.Score) -> Sequence[Union[AST.Note, AST.Rest]]:
        """Perform visiting operation on Score node."""
        return [y for x in score.measures for y in x.accept(self)]

    def visit_note(self, note: AST.Note) -> Sequence[Union[AST.Note, AST.Rest]]:
        """Perform visiting operation on Note node."""
        return [note]

    def visit_toplevel(
        self, toplevel: AST.TopLevel
    ) -> Sequence[Union[AST.Note, AST.Rest]]:
        """Perform visiting operation on TopLevel node."""
        return []

    def visit_token(self, token: AST.Token) -> Sequence[Union[AST.Note, AST.Rest]]:
        """Perform visiting operation on Token node."""
        return []

    def visit_chord(self, chord: AST.Chord) -> Sequence[Union[AST.Note, AST.Rest]]:
        """Perform visiting operation on Chord node."""
        return chord.notes

    def visit_rest(self, rest: AST.Rest) -> Sequence[Union[AST.Note, AST.Rest]]:
        """Perform visiting operation on Rest node."""
        return [rest]

    def visit_note_group(
        self, note_group: AST.NoteGroup
    ) -> Sequence[Union[AST.Note, AST.Rest]]:
        """Perform visiting operation on NoteGroup node."""
        return [y for x in note_group.children for y in x.accept(self)]

    def visit_attributes(
        self, attributes: AST.Attributes
    ) -> Sequence[Union[AST.Note, AST.Rest]]:
        """Perform visiting operation on Attributes node."""
        return []

    def visit_time_signature(
        self, time_signature: AST.TimeSignature
    ) -> Sequence[Union[AST.Note, AST.Rest]]:
        """Perform visiting operation on TimeSignature node."""
        return []

    def visit_key(self, key: AST.Key) -> Sequence[Union[AST.Note, AST.Rest]]:
        """Perform visiting operation on Key node."""
        return []

    def visit_clef(self, clef: AST.Clef) -> Sequence[Union[AST.Note, AST.Rest]]:
        """Perform visiting operation on Clef node."""
        return []

    def visit_direction(
        self, direction: AST.Direction
    ) -> Sequence[Union[AST.Note, AST.Rest]]:
        """Perform visiting operation on Direction node."""
        return []

    def visit_measure(
        self, measure: AST.Measure
    ) -> Sequence[Union[AST.Note, AST.Rest]]:
        """Perform visiting operation on Measure node."""
        return [y for x in measure.elements for y in x.accept(self)]

    def visit_barline(
        self, barline: AST.Barline
    ) -> Sequence[Union[AST.Note, AST.Rest]]:
        """Perform visiting operation on Barline node."""
        return []

    def visit_tuplet(self, tuplet: AST.Tuplet) -> Sequence[Union[AST.Note, AST.Rest]]:
        """Perform visiting operation on Tuplet node."""
        return []

    def visit_numerator(
        self, numerator: AST.Numerator
    ) -> Sequence[Union[AST.Note, AST.Rest]]:
        """Perform visiting operation on Numerator node."""
        return []

    def visit_denominator(
        self, denominator: AST.Denominator
    ) -> Sequence[Union[AST.Note, AST.Rest]]:
        """Perform visiting operation on Denominator node."""
        return []

    def visit_number(self, number: AST.Number) -> Sequence[Union[AST.Note, AST.Rest]]:
        """Perform visiting operation on Number node."""
        return []

    def visit_timesig_fraction(
        self, fraction: AST.TimesigFraction
    ) -> Sequence[Union[AST.Note, AST.Rest]]:
        """Perform visiting operation on timesig fraction node."""
        return []
