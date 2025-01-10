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
Implementation of a visitor that converts the MTN objects into an XML representation.
"""

import xml.etree.ElementTree as ET
from typing import List, Mapping, Sequence

from .mtn import ast as AST
from .mtn import types as TT


class VisitorToXML(AST.Visitor):
    """Implements conversion to MTN XML."""

    def __init__(self, ignore_id=False):
        super().__init__()

        self.ignore_id = ignore_id

    def _accept_and_append_children(
        self,
        root: ET.Element,
        children: Sequence[AST.SyntaxNode],
    ) -> None:
        for child in children:
            subelement = child.accept(self)
            root.append(subelement)

    def visit_ast(self, root: AST.SyntaxNode) -> ET.Element:
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

    def visit_note(self, note: AST.Note) -> ET.Element:
        """Perform visiting operation on Note node."""
        element = ET.Element("note")
        note_element = note.notehead.accept(self)
        element.append(note_element)

        self._accept_and_append_children(element, note.dots)
        self._accept_and_append_children(element, note.accidentals)
        self._accept_and_append_children(element, note.modifiers)

        for ch in element:
            if ch is not note_element:
                if "staff" in ch.attrib:
                    del ch.attrib["staff"]
                if "position" in ch.attrib:
                    del ch.attrib["position"]

        return element

    def visit_toplevel(self, toplevel: AST.TopLevel) -> ET.Element:
        """Perform visiting operation on TopLevel node."""
        raise NotImplementedError()

    def visit_token(self, token: AST.Token) -> ET.Element:
        """Perform visiting operation on Token node."""
        name = token.token_type.value
        modifiers = {
            k: str(v.value) if hasattr(v, "value") else str(v)
            for k, v in token.modifiers.items()
        }

        staff, pos = token.position

        if token.token_type in {
            TT.TokenType.NOTEHEAD,
            TT.TokenType.REST,
            TT.TokenType.ACCIDENTAL,
            TT.TokenType.CLEF,
        }:
            if staff is not None and token.token_type != TT.TokenType.ACCIDENTAL:
                modifiers["staff"] = str(staff)
            if pos is not None:
                modifiers["position"] = str(pos)
        if not self.ignore_id:
            modifiers["id"] = str(token.token_id)

        return ET.Element(name, attrib=modifiers)

    def visit_chord(self, chord: AST.Chord) -> ET.Element:
        """Perform visiting operation on Chord node."""
        element = ET.Element("chord", {"delta": str(chord.delta)})
        if chord.stem is not None:
            stem_element = chord.stem.accept(self)
            element.append(stem_element)
        self._accept_and_append_children(element, chord.notes)

        return element

    def visit_rest(self, rest: AST.Rest) -> ET.Element:
        """Perform visiting operation on Rest node."""
        element = ET.Element("rest", attrib={"delta": str(rest.delta)})
        rest_element = rest.rest_token.accept(self)
        element.append(rest_element)

        self._accept_and_append_children(element, rest.dots)
        self._accept_and_append_children(element, rest.modifiers)

        return element

    def visit_note_group(self, note_group: AST.NoteGroup) -> ET.Element:
        """Perform visiting operation on NoteGroup node."""
        element = ET.Element("note_group", attrib={"delta": str(note_group.delta)})
        self._accept_and_append_children(element, note_group.appendages)
        self._accept_and_append_children(element, note_group.children)

        return element

    def _process_attr_dict(
        self, root: ET.Element, attr_dict: Mapping[int, AST.SyntaxNode | None]
    ) -> None:
        for ii in sorted(attr_dict.keys()):
            elm = attr_dict[ii]
            if elm is not None:
                result = elm.accept(self)
                if result is not None:
                    result.attrib["staff"] = str(ii)
                    root.append(result)

    def visit_attributes(self, attributes: AST.Attributes) -> ET.Element:
        """Perform visiting operation on Attributes node."""
        element = ET.Element("attributes", attrib={"delta": str(attributes.delta)})
        self._process_attr_dict(element, attributes.clef)
        self._process_attr_dict(element, attributes.key)
        self._process_attr_dict(element, attributes.timesig)
        return element

    def visit_time_signature(
        self, time_signature: AST.TimeSignature
    ) -> ET.Element | None:
        """Perform visiting operation on TimeSignature node."""
        element = ET.Element("time_signature")

        if time_signature.time_symbol is not None:
            element.append(time_signature.time_symbol.accept(self))

        elif time_signature.compound_time_signature is not None:
            for child in time_signature.compound_time_signature:
                output = child.accept(self)

                if isinstance(output, list):
                    for x in output:
                        element.append(x)
                elif isinstance(output, ET.Element):
                    element.append(output)
                else:
                    raise ValueError("Invalid type under time signature")
        else:
            return None

        return element

    def visit_key(self, key: AST.Key) -> ET.Element | None:
        """Perform visiting operation on Key node."""
        element = ET.Element("key")

        if len(key.naturals) == 0 and len(key.accidentals) == 0:
            return None

        self._accept_and_append_children(element, key.naturals)
        self._accept_and_append_children(element, key.accidentals)

        return element

    def visit_clef(self, clef: AST.Clef) -> ET.Element | None:
        """Perform visiting operation on Clef node."""
        if clef.clef_token is not None:
            return clef.clef_token.accept(self)
        return None

    def visit_direction(self, direction: AST.Direction) -> ET.Element:
        """Perform visiting operation on Direction node."""
        element = ET.Element("direction", attrib={"delta": str(direction.delta)})

        self._accept_and_append_children(element, direction.directives)

        return element

    def visit_measure(self, measure: AST.Measure) -> ET.Element:
        """Perform visiting operation on Measure node."""
        element = ET.Element(
            "measure",
            attrib={
                "part_id": measure.part_id,
                "measure_id": measure.measure_id,
                "staves": str(measure.staves),
            },
        )
        if measure.left_barline is not None:
            element.append(measure.left_barline.accept(self))
        self._accept_and_append_children(element, measure.elements)
        if measure.right_barline is not None:
            element.append(measure.right_barline.accept(self))

        return element

    def visit_barline(self, barline: AST.Barline) -> ET.Element:
        """Perform visiting operation on Barline node."""
        element = ET.Element("barline", attrib={"delta": str(barline.delta)})

        self._accept_and_append_children(element, barline.barline_tokens)
        self._accept_and_append_children(element, barline.modifiers)

        return element

    def visit_numerator(self, numerator: AST.Numerator) -> ET.Element:
        """Perform visiting operation on Numerator node."""
        element = ET.Element("numerator")

        for child in numerator.digits_or_sum:
            if isinstance(child, AST.Token):
                element.append(child.accept(self))
            elif isinstance(child, AST.Number):
                for digit in child.accept(self):
                    element.append(digit)
        return element

    def visit_denominator(self, denominator: AST.Denominator) -> ET.Element:
        """Perform visiting operation on Denominator node."""
        element = ET.Element("denominator")

        for num in denominator.digits.accept(self):
            element.append(num)
        return element

    def visit_number(self, number: AST.Number) -> List[ET.Element]:
        """Perform visiting operation on Number node."""
        return [x.accept(self) for x in number.digits]

    def visit_timesig_fraction(self, fraction: AST.TimesigFraction) -> List[ET.Element]:
        """Perform visiting operation on timesig fraction node."""
        output = [fraction.numerator.accept(self)]

        if fraction.denominator is not None:
            output.append(fraction.denominator.accept(self))
        return output

    def visit_score(self, score: AST.Score) -> ET.Element:
        """Perform visiting operation on timesig score node."""
        element = ET.Element("score", attrib={"id": score.score_id})

        for measure in score.measures:
            element.append(measure.accept(self))
        return element

    def visit_tuplet(self, tuplet: AST.Tuplet) -> ET.Element:
        """Perform visiting operation on tuplet node."""
        element = ET.Element("tuplet")

        if tuplet.number is not None:
            for x in tuplet.number.accept(self):
                element.append(x)
        element.append(tuplet.tuplet.accept(self))

        return element
