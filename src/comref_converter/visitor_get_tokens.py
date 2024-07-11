"""The Common Optical Music Recognition Framework (COMReF) toolset.

Get all token nodes in the MTN AST.

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


from typing import List

from .mtn import ast as AST


class VisitorGetTokens(AST.Visitor):
    """Recovers all tokens in a tree."""

    def visit_ast(self, root: AST.SyntaxNode) -> List[AST.Token]:
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

    def visit_note(self, note: AST.Note) -> List[AST.Token]:
        """Perform visiting operation on Note node."""
        modifiers = [y for x in note.modifiers for y in x.accept(self)]
        return [
            note.notehead,
            *note.dots,
            *note.accidentals,
            *modifiers,
        ]

    def visit_tuplet(self, tuplet: AST.Tuplet) -> List[AST.Token]:
        """Perform visiting operation on Tuplet node."""
        if tuplet.number is not None:
            digits = [y for y in tuplet.number.accept(self)]
        else:
            digits = []
        return [*digits, tuplet.tuplet]

    def visit_number(self, number: AST.Number) -> List[AST.Token]:
        """Perform visiting operation on Number node."""
        return number.digits

    def visit_denominator(self, denominator: AST.Denominator) -> List[AST.Token]:
        """Perform visiting operation on Denominator node."""
        return denominator.digits.accept(self)

    def visit_numerator(self, numerator: AST.Numerator) -> List[AST.Token]:
        """Perform visiting operation on Numerator node."""
        return [y for x in numerator.digits_or_sum for y in x.accept(self)]

    def visit_timesig_fraction(self, fraction: AST.TimesigFraction) -> List[AST.Token]:
        """Perform visiting operation on Fraction node."""
        return [
            *fraction.numerator.accept(self),
            *(
                fraction.denominator.accept(self)
                if fraction.denominator is not None
                else []
            ),
        ]

    def visit_chord(self, chord: AST.Chord) -> List[AST.Token]:
        """Perform visiting operation on Chord node."""
        base = []
        if chord.stem is not None:
            base.append(chord.stem)
        return base + [y for x in chord.notes for y in x.accept(self)]

    def visit_rest(self, rest: AST.Rest) -> List[AST.Token]:
        """Perform visiting operation on Rest node."""
        modifiers = [y for x in rest.modifiers for y in x.accept(self)]

        return [rest.rest_token, *rest.dots, *modifiers]

    def visit_note_group(self, note_group: AST.NoteGroup) -> List[AST.Token]:
        """Perform visiting operation on NoteGroup node."""
        output = []
        for child in note_group.children:
            output += child.accept(self)

        output += note_group.appendages
        return output

    def visit_attributes(self, attributes: AST.Attributes) -> List[AST.Token]:
        """Perform visiting operation on Attributes node."""
        output = []

        for key in attributes.key.values():
            if key is not None:
                output += key.accept(self)

        for clef in attributes.clef.values():
            if clef is not None:
                output += clef.accept(self)

        for timesig in attributes.timesig.values():
            if timesig is not None:
                output += timesig.accept(self)

        return output

    def visit_time_signature(
        self, time_signature: AST.TimeSignature
    ) -> List[AST.Token]:
        """Perform visiting operation on TimeSignature node."""
        output = []
        if time_signature.time_symbol is not None:
            output.append(time_signature.time_symbol)
        elif time_signature.compound_time_signature is not None:
            for x in time_signature.compound_time_signature:
                output += x.accept(self)
        return output

    def visit_key(self, key: AST.Key) -> List[AST.Token]:
        """Perform visiting operation on Key node."""
        return key.naturals + key.accidentals

    def visit_clef(self, clef: AST.Clef) -> List[AST.Token]:
        """Perform visiting operation on Clef node."""
        return [clef.clef_token] if clef.clef_token is not None else []

    def visit_direction(self, direction: AST.Direction) -> List[AST.Token]:
        """Perform visiting operation on Direction node."""
        return direction.directives

    def visit_measure(self, measure: AST.Measure) -> List[AST.Token]:
        """Perform visiting operation on Measure node."""
        output = []
        if measure.left_barline is not None:
            output.extend(measure.left_barline.accept(self))
        for x in measure.elements:
            output += x.accept(self)
        if measure.right_barline is not None:
            output.extend(measure.right_barline.accept(self))
        return output

    def visit_barline(self, barline: AST.Barline) -> List[AST.Token]:
        """Perform visiting operation on Barline node."""
        return barline.barline_tokens + barline.modifiers

    def visit_token(self, token: AST.Token) -> List[AST.Token]:
        """Return token embedded in a list. Useful to use accept on sum type."""
        return [token]

    def visit_toplevel(self, toplevel: AST.TopLevel) -> List[AST.Token]:
        """Must never be used in this context."""
        raise NotImplementedError()

    def visit_score(self, score: AST.Score) -> List[AST.Token]:
        """Visit a score element."""
        return [y for x in score.measures for y in x.accept(self)]
