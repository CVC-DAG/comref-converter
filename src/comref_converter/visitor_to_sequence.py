"""The Common Optical Music Recognition Framework (COMReF) toolset.

Convert MTN representation into model-readable sequence of tokens.

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

from fractions import Fraction
from typing import Any, Dict, List

from .mtn import ast as AST
from .translator_base import MeasureID


class VisitorToModelSequence(AST.Visitor):
    """Implements conversion to a model-readable sequence."""

    def __init__(
        self,
        stateful_parsing: bool = True,
        simple_numbers: bool = True,
    ) -> None:
        """Construct Visitor.

        Parameters
        ----------
        stateful_parsing : bool, optional
            Whether the object will take into account the last seen delta to omit it
            during generation if redundant. For example, if there are two notegroups on
            the same
        simple_numbers: bool, optional
            Whether number tokens will be generated with their corresponding
        """
        super().__init__()

        self.stateful_parsing = stateful_parsing
        self.simple_numbers = simple_numbers

        self.last_time = Fraction(0)

    def visit_ast(self, root: AST.SyntaxNode) -> List[str]:
        """Perform conversion of an MTN tree into a set of JSON-like dictionaries.

        Parameters
        ----------
        root: AST.SyntaxNode
            Any subtree to convert to dictionaries.

        Returns
        -------
        Dict
            Set of dictionaries with the MTN tree in JSON-like format.
        """
        return root.accept(self)

    def visit_score(self, score: AST.Score) -> Dict[MeasureID, List[str]]:
        """Perform visiting operation on Score node."""
        return {k: v for x in score.measures for k, v in x.accept(self).items()}

    def visit_note(self, note: AST.Note) -> List[str]:
        """Perform visiting operation on Note node."""
        output = []

        output.extend(note.notehead.accept(self))

        output.extend([x for dot in note.dots for x in dot.accept(self)])
        output.extend(
            [x for accidental in note.accidentals for x in accidental.accept(self)]
        )
        output.extend([x for modifier in note.modifiers for x in modifier.accept(self)])

        return output

    def visit_toplevel(self, toplevel: AST.TopLevel) -> List[str]:
        """Perform visiting operation on TopLevel node."""
        if self.stateful_parsing and toplevel.delta == self.last_time:
            return []
        self.last_time = toplevel.delta
        return [f"delta:{str(toplevel.delta)}"]

    def visit_token(self, token: AST.Token) -> List[str]:
        """Perform visiting operation on Token node."""
        if self.simple_numbers and token.token_type == AST.TT.TokenType.NUMBER:
            return [str(token.modifiers["type"].value)]

        output = f"{token.token_type.value}"

        if len(token.modifiers) != 0:
            output += ":"
            output += "&".join(
                [
                    f"{k}={v.value if hasattr(v, 'value') else str(v)}"
                    for k, v in token.modifiers.items()
                ]
            )
        output_list = [output]

        if (
            token.token_type == AST.TT.TokenType.NOTEHEAD
            and token.position.staff is not None
        ):
            output_list.append(f"staff:{token.position.staff}")
        if (
            token.token_type in {AST.TT.TokenType.NOTEHEAD, AST.TT.TokenType.ACCIDENTAL}
            and token.position.position is not None
        ):
            output_list.append(f"position:{token.position.position}")

        return output_list

    def visit_chord(self, chord: AST.Chord) -> List[str]:
        """Perform visiting operation on Chord node."""
        output = []
        if chord.stem is not None:
            output.extend(chord.stem.accept(self))
        output.extend([y for x in chord.notes for y in x.accept(self)])
        return output

    def visit_rest(self, rest: AST.Rest) -> List[str]:
        """Perform visiting operation on Rest node."""
        output = self.visit_toplevel(rest)
        output.extend(rest.rest_token.accept(self))
        output.extend([y for x in rest.dots for y in x.accept(self)])
        output.extend([y for x in rest.modifiers for y in x.accept(self)])

        return output

    def visit_note_group(self, note_group: AST.NoteGroup) -> List[str]:
        """Perform visiting operation on NoteGroup node."""
        output = self.visit_toplevel(note_group)
        output.append("group:begin")
        output.extend([y for x in note_group.appendages for y in x.accept(self)])
        output.extend([y for x in note_group.children for y in x.accept(self)])
        output.append("group:end")

        return output

    def visit_attributes(self, attributes: AST.Attributes) -> List[str]:
        """Perform visiting operation on Attributes node."""
        output = self.visit_toplevel(attributes)
        output.append("attributes")

        for staff in range(1, attributes.nstaves + 1):
            clef = attributes.get_clef(staff)
            key = attributes.get_key(staff)
            timesig = attributes.get_timesig(staff)
            if any(map(lambda x: x is not None, [key, clef, timesig])):
                output.append(f"staff:{staff}")
            if clef is not None:
                output.extend(clef.accept(self))
            if key is not None:
                output.extend(key.accept(self))
            if timesig is not None:
                output.extend(timesig.accept(self))
        return output

    def visit_time_signature(self, time_signature: AST.TimeSignature) -> List[str]:
        """Perform visiting operation on TimeSignature node."""
        output = []
        if time_signature.time_symbol is not None:
            output.extend(time_signature.time_symbol.accept(self))
        elif time_signature.compound_time_signature is not None:
            output.extend(
                [
                    y
                    for x in time_signature.compound_time_signature
                    for y in x.accept(self)
                ]
            )

        return output

    def visit_key(self, key: AST.Key) -> List[str]:
        """Perform visiting operation on Key node."""
        output = []
        output.extend([y for x in key.naturals for y in x.accept(self)])
        output.extend([y for x in key.accidentals for y in x.accept(self)])
        return output

    def visit_clef(self, clef: AST.Clef) -> List[str]:
        """Perform visiting operation on Clef node."""
        if clef.clef_token is not None:
            return clef.clef_token.accept(self)
        return []

    def visit_direction(self, direction: AST.Direction) -> List[str]:
        """Perform visiting operation on Direction node."""
        output = self.visit_toplevel(direction)
        output.append("directions")
        output.extend([y for x in direction.directives for y in x.accept(self)])
        return output

    def visit_measure(self, measure: AST.Measure) -> Dict[MeasureID, List[str]]:
        """Perform visiting operation on Measure node."""
        output = []

        if measure.left_barline is not None:
            output.extend(measure.left_barline.accept(self))

        output.extend([y for x in measure.elements for y in x.accept(self)])

        if measure.right_barline is not None:
            output.extend(measure.right_barline.accept(self))
        self.last_time = Fraction(0)
        return {(measure.part_id, measure.measure_id): output}

    def visit_barline(self, barline: AST.Barline) -> List[str]:
        """Perform visiting operation on Barline node."""
        output = self.visit_toplevel(barline)
        output.extend([y for x in barline.barline_tokens for y in x.accept(self)])
        output.extend([y for x in barline.modifiers for y in x.accept(self)])

        return output

    def visit_tuplet(self, tuplet: AST.Tuplet) -> List[str]:
        """Perform visiting operation on Tuplet node."""
        output = []
        output.extend(tuplet.tuplet.accept(self))
        if tuplet.number is not None:
            if self.simple_numbers:
                output[0] += "&" + tuplet.number.accept(self)[0]
            else:
                output.extend(tuplet.number.accept(self))
        return output

    def visit_numerator(self, numerator: AST.Numerator) -> List[str]:
        """Perform visiting operation on Numerator node."""
        return [y for x in numerator.digits_or_sum for y in x.accept(self)]

    def visit_denominator(self, denominator: AST.Denominator) -> List[str]:
        """Perform visiting operation on Denominator node."""
        return denominator.digits.accept(self)

    def visit_number(self, number: AST.Number) -> List[str]:
        """Perform visiting operation on Number node."""
        return [y for x in number.digits for y in x.accept(self)]

    def visit_timesig_fraction(self, fraction: AST.TimesigFraction) -> List[str]:
        """Perform visiting operation on timesig fraction node."""
        output = ["("]
        output.extend(fraction.numerator.accept(self))
        if fraction.denominator is not None:
            output.append("/")
            output.extend(fraction.denominator.accept(self))
        output.append(")")
        if self.simple_numbers:
            return ["".join(output)]
        return output
