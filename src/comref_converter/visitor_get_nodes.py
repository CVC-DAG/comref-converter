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
An iterator over all nodes in the tree in MTN order.
"""

from typing import List

from .mtn import ast as AST


class VisitorGetNodes(AST.Visitor):
    """Recovers all tokens in a tree."""

    def visit_ast(self, root: AST.SyntaxNode) -> List[AST.SyntaxNode]:
        """Perform conversion of an MTN tree into MTN XML.

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

    def visit_note(self, note: AST.Note) -> List[AST.SyntaxNode]:
        """Perform visiting operation on Note node."""
        return [
            note,
            note.notehead,
            *note.dots,
            *note.accidentals,
        ] + [y for x in note.modifiers for y in x.accept(self)]

    def visit_tuplet(self, tuplet: AST.Tuplet) -> List[AST.SyntaxNode]:
        """Perform visiting operation on Tuplet node."""
        output: List[AST.SyntaxNode] = [tuplet]
        if tuplet.number is not None:
            output.extend(tuplet.number.accept(self))
        output.append(tuplet.tuplet)
        return output

    def visit_number(self, number: AST.Number) -> List[AST.SyntaxNode]:
        """Perform visiting operation on Number node."""
        output: List[AST.SyntaxNode] = [number]
        return output + number.digits

    def visit_denominator(self, denominator: AST.Denominator) -> List[AST.SyntaxNode]:
        """Perform visiting operation on Denominator node."""
        output: List[AST.SyntaxNode] = [denominator]
        output.extend(denominator.digits.accept(self))
        return output

    def visit_numerator(self, numerator: AST.Numerator) -> List[AST.SyntaxNode]:
        """Perform visiting operation on Numerator node."""
        output: List[AST.SyntaxNode] = [numerator]
        output.extend([y for x in numerator.digits_or_sum for y in x.accept(self)])
        return output

    def visit_timesig_fraction(
        self, fraction: AST.TimesigFraction
    ) -> List[AST.SyntaxNode]:
        """Perform visiting operation on Fraction node."""
        output: List[AST.SyntaxNode] = [fraction]
        output.extend(fraction.numerator.accept(self))
        if fraction.denominator is not None:
            output.extend(fraction.denominator.accept(self))
        return output

    def visit_chord(self, chord: AST.Chord) -> List[AST.SyntaxNode]:
        """Perform visiting operation on Chord node."""
        output: List[AST.SyntaxNode] = [chord]
        if chord.stem is not None:
            output.append(chord.stem)
        output.extend([y for x in chord.notes for y in x.accept(self)])
        return output

    def visit_rest(self, rest: AST.Rest) -> List[AST.SyntaxNode]:
        """Perform visiting operation on Rest node."""
        output: List[AST.SyntaxNode] = [rest]
        output.append(rest.rest_token)
        output.extend(rest.dots)
        output.extend([y for x in rest.modifiers for y in x.accept(self)])

        return output

    def visit_note_group(self, note_group: AST.NoteGroup) -> List[AST.SyntaxNode]:
        """Perform visiting operation on NoteGroup node."""
        output: List[AST.SyntaxNode] = [note_group]
        output.extend([y for x in note_group.children for y in x.accept(self)])
        output.extend(note_group.appendages)
        return output

    def visit_attributes(self, attributes: AST.Attributes) -> List[AST.SyntaxNode]:
        """Perform visiting operation on Attributes node."""
        output: List[AST.SyntaxNode] = [attributes]

        for key in attributes.key.values():
            if key is not None:
                output.extend(key.accept(self))

        for clef in attributes.clef.values():
            if clef is not None:
                output.extend(clef.accept(self))

        for timesig in attributes.timesig.values():
            if timesig is not None:
                output.extend(timesig.accept(self))

        return output

    def visit_time_signature(
        self, time_signature: AST.TimeSignature
    ) -> List[AST.SyntaxNode]:
        """Perform visiting operation on TimeSignature node."""
        output: List[AST.SyntaxNode] = [time_signature]
        if time_signature.time_symbol is not None:
            output.append(time_signature.time_symbol)
        elif time_signature.compound_time_signature is not None:
            for x in time_signature.compound_time_signature:
                output += x.accept(self)
        return output

    def visit_key(self, key: AST.Key) -> List[AST.SyntaxNode]:
        """Perform visiting operation on Key node."""
        output: List[AST.SyntaxNode] = [key]
        output.extend(key.naturals)
        output.extend(key.accidentals)
        return output

    def visit_clef(self, clef: AST.Clef) -> List[AST.SyntaxNode]:
        """Perform visiting operation on Clef node."""
        output: List[AST.SyntaxNode] = [clef]
        if clef.clef_token is not None:
            output.append(clef.clef_token)
        return output

    def visit_direction(self, direction: AST.Direction) -> List[AST.SyntaxNode]:
        """Perform visiting operation on Direction node."""
        output: List[AST.SyntaxNode] = [direction]
        output.extend(direction.directives)
        return output

    def visit_measure(self, measure: AST.Measure) -> List[AST.SyntaxNode]:
        """Perform visiting operation on Measure node."""
        output: List[AST.SyntaxNode] = [measure]
        if measure.left_barline is not None:
            output.extend(measure.left_barline.accept(self))
        for x in measure.elements:
            output.extend(x.accept(self))
        if measure.right_barline is not None:
            output.extend(measure.right_barline.accept(self))
        return output

    def visit_barline(self, barline: AST.Barline) -> List[AST.SyntaxNode]:
        """Perform visiting operation on Barline node."""
        output: List[AST.SyntaxNode] = [barline]
        output.extend(barline.barline_tokens)
        output.extend(barline.modifiers)
        return output

    def visit_token(self, token: AST.Token) -> List[AST.SyntaxNode]:
        """Return token embedded in a list. Useful to use accept on sum type."""
        return [token]

    def visit_toplevel(self, toplevel: AST.TopLevel) -> List[AST.SyntaxNode]:
        """Must never be used in this context."""
        raise NotImplementedError()

    def visit_score(self, score: AST.Score) -> List[AST.SyntaxNode]:
        """Visit a score element."""
        output: List[AST.SyntaxNode] = [score]
        output.extend([y for x in score.measures for y in x.accept(self)])
        return output
