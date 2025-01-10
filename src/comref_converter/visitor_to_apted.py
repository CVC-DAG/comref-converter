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
Convert MTN AST into an APTED tree representation for Tree Edit Distance computations.
"""

from .mtn import ast as AST


class VisitorToAPTED(AST.Visitor):
    """Convert tree into string representation for evaluation."""

    def __init__(self) -> None:
        super().__init__()

    def visit_toplevel(self, toplevel: AST.TopLevel) -> str:
        """Perform visiting operation on TopLevel node."""
        return ""

    def visit_score(self, score: AST.Score) -> str:
        """Perform visiting operation on Score node."""
        output = {}
        for measure in score.measures:
            output[(measure.part_id, measure.measure_id)] = measure.accept(self)

        return "\n".join([f"{str(k)}: {str(v)}" for k, v in output.items()])

    def visit_ast(self, root: AST.SyntaxNode) -> str:
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

    def visit_note(self, note: AST.Note) -> str:
        """Perform visiting operation on Note node."""
        output = "note"
        output += note.notehead.accept(self)
        output += "".join([x.accept(self) for x in note.dots])
        output += "".join([x.accept(self) for x in note.accidentals])
        output += "".join([x.accept(self) for x in note.modifiers])

        return self._parenthesise(output)

    def visit_token(self, token: AST.Token) -> str:
        """Perform visiting operation on Token node."""
        output = token.token_type.value
        key_names = sorted(token.modifiers.keys())
        mods = token.modifiers
        modifiers = "_".join(
            [
                (
                    k
                    if isinstance(mods[k], bool)
                    else (
                        str(mods[k].value)
                        if hasattr(mods[k], "value")
                        else str(mods[k])
                    )
                )
                for k in key_names
            ]
        )

        return self._parenthesise(output + ("_" * (len(modifiers) > 0)) + modifiers)

    def visit_chord(self, chord: AST.Chord) -> str:
        """Perform visiting operation on Chord node."""
        output = "chord"

        children = []
        if chord.stem is not None:
            children.append(chord.stem.accept(self))
        for child in chord.notes:
            children.append(child.accept(self))

        return self._parenthesise(output + "".join(children))

    def visit_rest(self, rest: AST.Rest) -> str:
        """Perform visiting operation on Rest node."""
        output = "rest" + rest.rest_token.accept(self)
        output += "".join([x.accept(self) for x in rest.dots])
        output += "".join([x.accept(self) for x in rest.modifiers])

        return self._parenthesise(output)

    def visit_note_group(self, note_group: AST.NoteGroup) -> str:
        """Perform visiting operation on NoteGroup node."""
        output = "group"
        output += "".join([x.accept(self) for x in note_group.appendages])
        output += "".join([x.accept(self) for x in note_group.children])

        return self._parenthesise(output)

    def visit_attributes(self, attributes: AST.Attributes) -> str:
        """Perform visiting operation on Attributes node."""
        output = "attributes"
        for ii in sorted(attributes.key.keys()):
            key = attributes.key[ii]
            if key is not None:
                output += key.accept(self)
        for ii in sorted(attributes.clef.keys()):
            clef = attributes.clef[ii]
            if clef is not None:
                output += clef.accept(self)
        for ii in sorted(attributes.timesig.keys()):
            timesig = attributes.timesig[ii]
            if timesig is not None:
                output += timesig.accept(self)
        return self._parenthesise(output)

    def visit_time_signature(self, time_signature: AST.TimeSignature) -> str:
        """Perform visiting operation on TimeSignature node."""
        output = "time_signature"
        if time_signature.time_symbol is not None:
            output += time_signature.time_symbol.accept(self)

        if time_signature.compound_time_signature is not None:
            for child in time_signature.compound_time_signature:
                output += child.accept(self)

        return self._parenthesise(output)

    def visit_key(self, key: AST.Key) -> str:
        """Perform visiting operation on Key node."""
        output = "key"
        output += "".join([x.accept(self) for x in key.accidentals])
        output += "".join([x.accept(self) for x in key.naturals])

        return self._parenthesise(output)

    def visit_clef(self, clef: AST.Clef) -> str:
        """Perform visiting operation on Clef node."""
        output = "clef"
        if clef.clef_token is not None:
            output += clef.clef_token.accept(self)
            return self._parenthesise(output)
        else:
            return ""

    def visit_direction(self, direction: AST.Direction) -> str:
        """Perform visiting operation on Direction node."""
        output = "direction"

        for child in direction.directives:
            output += child.accept(self)
        return self._parenthesise(output)

    def visit_measure(self, measure: AST.Measure) -> str:
        """Perform visiting operation on Measure node."""
        output = "measure"
        if measure.left_barline is not None:
            output += measure.left_barline.accept(self)
        for child in measure.elements:
            output += child.accept(self)
        if measure.right_barline is not None:
            output += measure.right_barline.accept(self)

        return self._parenthesise(output)

    def visit_barline(self, barline: AST.Barline) -> str:
        """Perform visiting operation on Barline node."""
        output = "barline"
        output += "".join([x.accept(self) for x in barline.barline_tokens])
        output += "".join([x.accept(self) for x in barline.modifiers])

        return self._parenthesise(output)

    def visit_tuplet(self, tuplet: AST.Tuplet) -> str:
        """Perform visiting operation on Tuplet node."""
        output = "tuplet"
        output += tuplet.tuplet.accept(self)
        if tuplet.number is not None:
            output += tuplet.number.accept(self)

        return self._parenthesise(output)

    def visit_numerator(self, numerator: AST.Numerator) -> str:
        """Perform visiting operation on Numerator node."""
        output = "numerator"
        output += "".join([x.accept(self) for x in numerator.digits_or_sum])

        return self._parenthesise(output)

    def visit_denominator(self, denominator: AST.Denominator) -> str:
        """Perform visiting operation on Denominator node."""
        output = "numerator"
        output += denominator.digits.accept(self)

        return self._parenthesise(output)

    def visit_number(self, number: AST.Number) -> str:
        """Perform visiting operation on Number node."""
        output = "number"
        output += "".join([x.accept(self) for x in number.digits])

        return self._parenthesise(output)

    def visit_timesig_fraction(self, fraction: AST.TimesigFraction) -> str:
        """Perform visiting operation on timesig fraction node."""
        output = "fraction"
        output += fraction.numerator.accept(self)
        if fraction.denominator is not None:
            output += fraction.denominator.accept(self)

        return self._parenthesise(output)

    def _parenthesise(self, sub: str) -> str:
        return "{" + sub + "}"
