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
Implementation of loading of the XML representation of MTN.
"""

from fractions import Fraction
from typing import (Any, Callable, Dict, List, Optional, Set, Type, TypeVar,
                    Union, cast)
from xml.etree import ElementTree as ET

from .mtn import ast as AST
from .mtn import semantics as MS
from .mtn import types as TT
from .translator_base import MeasureID, Translator

CLEF_TYPE2SIGN: Dict[TT.ClefType, TT.NamedPitch] = {
    TT.ClefType.CLEF_G: TT.NamedPitch.G,
    TT.ClefType.CLEF_C: TT.NamedPitch.C,
    TT.ClefType.CLEF_F: TT.NamedPitch.F,
    TT.ClefType.CLEF_PERCUSSION: TT.NamedPitch.G,
}


CLASS_TYPE: Dict[TT.TokenType, Type] = {
    TT.TokenType.ACCIDENTAL: TT.AccidentalType,
    TT.TokenType.BARLINE: TT.BarlineType,
    TT.TokenType.CLEF: TT.ClefType,
    TT.TokenType.DYN: TT.DynamicsType,
    TT.TokenType.GLISSANDO: TT.StartStop,
    TT.TokenType.NOTEHEAD: TT.NoteheadType,
    TT.TokenType.NUMBER: TT.Digits,
    TT.TokenType.PEDAL: TT.StartStop,
    TT.TokenType.REPEAT: TT.BackwardForward,
    TT.TokenType.REST: TT.NoteType,
    TT.TokenType.SLIDE: TT.StartStop,
    TT.TokenType.SLUR: TT.StartStop,
    TT.TokenType.STEM: TT.StemDirection,
    TT.TokenType.TIED: TT.StartStop,
    TT.TokenType.TIME_RELATION: TT.TimeRelation,
    TT.TokenType.TIMESIG: TT.TimeSymbol,
    TT.TokenType.TUPLET: TT.StartStop,
    TT.TokenType.WEDGE: TT.WedgeType,
}


class TranslatorXML(Translator):
    """Translator from MTN XML to MTN."""

    def __init__(self) -> None:
        self.current_staves = 1

    def translate(
        self,
        score_in: ET.Element,
        score_id: str,
        engr_first_line: Set[MeasureID],
    ) -> AST.Score:
        """Translate a score MTN.

        Parameters
        ----------
        score_in : Any
            The representation of the input score in any supported type.
        score_id : str
            An identifier for the score being processed.
        engr_first_line : Set[MeasureID]
            Set of measure identifiers for those systems that lie at the beginning of a
            line (and thus need a refresh of clef and key elements).

        Returns
        -------
        MTN.AST.Score
            Representation of the score in MTN format.
        """
        return self._visit_score(score_in)

    def _visit_score(self, score: ET.Element) -> AST.Score:
        """Visit score node."""
        children = [self._visit_measure(measure) for measure in score]
        score_id = score.get("id", "<NULL>")

        return AST.Score(children, score_id)

    def _visit_measure(self, measure: ET.Element) -> AST.Measure:
        measure_id = measure.get("measure_id", "<NULL>")
        part_id = measure.get("part_id", "<NULL>")
        staves = maybe(measure.get("staves"), int)

        left_barline: Optional[AST.Barline] = None
        right_barline: Optional[AST.Barline] = None

        if staves is None:
            raise ValueError("Missing required staves attribute")
        self.current_staves = staves

        elements: List[AST.TopLevel] = []
        for ii, child in enumerate(measure):
            if child.tag == "rest":
                elements.append(self._visit_rest(child))
            elif child.tag == "note_group":
                elements.append(self._visit_note_group(child))
            elif child.tag == "barline":
                barline = self._visit_barline(child)
                if ii == 0:
                    left_barline = barline
                elif ii == len(measure) - 1:
                    right_barline = barline
                else:
                    elements.append(barline)
            elif child.tag == "direction":
                elements.append(self._visit_direction(child))
            elif child.tag == "attributes":
                elements.append(self._visit_attributes(child))

        output = AST.Measure(
            elements,
            left_barline,
            right_barline,
            staves,
            measure_id,
            part_id,
            Fraction(10),  # A priori it is not known
        )

        return output

    def _visit_attributes(self, attributes: ET.Element) -> AST.Attributes:
        delta = self._get_delta(attributes)
        key: Dict[int, AST.Key | None] = {
            ii: None for ii in range(1, self.current_staves + 1)
        }
        clef: Dict[int, AST.Clef | None] = {
            ii: None for ii in range(1, self.current_staves + 1)
        }
        timesig: Dict[int, AST.TimeSignature | None] = {
            ii: None for ii in range(1, self.current_staves + 1)
        }

        for child in attributes:
            staff = maybe(child.get("staff"), int)
            if staff is None:
                raise ValueError("Attributes element without a valid staff id.")

            if child.tag == "key":
                key_node = self._visit_key(child)
                key[staff] = key_node
            elif child.tag == "clef":
                clef_node = self._visit_clef(child)
                clef[staff] = clef_node
            elif child.tag == "time_signature":
                ts_node = self._visit_time_signature(child)
                timesig[staff] = ts_node
            else:
                raise ValueError("Invalid child in attributes node")

        return AST.Attributes(delta, self.current_staves, key, clef, timesig)

    def _visit_rest(self, rest: ET.Element) -> AST.Rest:
        delta = self._get_delta(rest)
        rest_token: AST.Token
        dots: List[AST.Token] = []
        modifiers: List[AST.Token | AST.Tuplet] = []

        for child in rest:
            if child.tag == "tuplet":
                modifiers.append(self._visit_tuplet(child))
            else:
                node = self._visit_token(child)
                if node.token_type == TT.TokenType.REST:
                    rest_token = node
                elif node.token_type == TT.TokenType.DOT:
                    dots.append(node)
                else:
                    modifiers.append(node)

        return AST.Rest(delta, rest_token, dots, modifiers)

    def _visit_direction(self, direction: ET.Element) -> AST.Direction:
        directives: List[AST.Token] = [self._visit_token(x) for x in direction]
        delta = self._get_delta(direction)

        return AST.Direction(delta, directives)

    def _visit_note_group(self, note_group: ET.Element) -> AST.NoteGroup:
        chords_or_groups: List[Union[AST.Chord, AST.NoteGroup]] = []
        beams_or_flags: List[AST.Token] = []
        delta = self._get_delta(note_group)
        for child in note_group:
            if child.tag == "note_group":
                chords_or_groups.append(self._visit_note_group(child))
            elif child.tag == "chord":
                chords_or_groups.append(self._visit_chord(child))
            elif child.tag in {"beam", "flag"}:
                beams_or_flags.append(self._visit_token(child))
        return AST.NoteGroup(
            delta,
            chords_or_groups,
            beams_or_flags,
        )

    def _visit_chord(self, chord: ET.Element) -> AST.Chord:
        delta = self._get_delta(chord)
        stem: Optional[AST.Token] = None
        notes: List[AST.Note] = []

        for child in chord:
            if child.tag == "stem":
                stem = self._visit_token(child)
            elif child.tag == "note":
                notes.append(self._visit_note(child))
        return AST.Chord(delta, stem, notes)

    def _visit_note(self, note: ET.Element) -> AST.Note:
        notehead: AST.Token | None = None
        dots: List[AST.Token] = []
        accidentals: List[AST.Token] = []
        modifiers: List[AST.Token | AST.Tuplet] = []

        for child in note:
            if child.tag == "tuplet":
                tuplet = self._visit_tuplet(child)
                modifiers.append(tuplet)
            else:
                token = self._visit_token(child)

                if token.token_type == TT.TokenType.NOTEHEAD:
                    notehead = token
                elif token.token_type == TT.TokenType.DOT:
                    dots.append(token)
                elif token.token_type == TT.TokenType.ACCIDENTAL:
                    accidentals.append(token)
                else:
                    modifiers.append(token)

        if notehead is None:
            raise ValueError("No notehead in note node")

        return AST.Note(notehead, dots, accidentals, modifiers)

    def _visit_barline(self, barline: ET.Element) -> AST.Barline:
        delta: Fraction = self._get_delta(barline)
        barline_tokens: List[AST.Token] = []
        modifiers: List[AST.Token] = []

        for child in barline:
            token = self._visit_token(child)

            if token.token_type == TT.TokenType.BARLINE:
                barline_tokens.append(token)
            else:
                modifiers.append(token)

        return AST.Barline(delta, barline_tokens, modifiers)

    def _visit_key(self, key: ET.Element) -> AST.Key:
        # TODO: Load up semantics of a key. This however depends on previously-seen
        # measures of the same part and requires processing parent nodes. It is to be
        # handled at some point in the future, but is not a priority now.
        accidentals: List[AST.Token] = []
        naturals: List[AST.Token] = []
        alterations: List[Optional[TT.AccidentalType]] = [
            None for _ in range(len(TT.NamedPitch))
        ]
        fifths: Optional[int] = self._get_fifths(key)
        staff = self._get_staff(key)

        for child in key:
            token = self._visit_token(child)
            token.position = MS.StaffPosition(staff, token.position.position)

            if token.modifiers["type"] == TT.AccidentalType.ACC_NATURAL:
                naturals.append(token)
            else:
                accidentals.append(token)

        return AST.Key(accidentals, naturals, alterations, fifths)

    def _visit_clef(self, clef: ET.Element) -> AST.Clef:
        clef_token: AST.Token = self._visit_token(clef)
        sign: TT.NamedPitch = CLEF_TYPE2SIGN[clef_token.modifiers["type"]]
        octave_mod = int(clef.get("oct", "0"))
        octave: int = MS.DEFAULT_CLEF_OCTAVE[sign] + octave_mod

        return AST.Clef(clef_token, sign, octave, clef_token.position)

    def _visit_time_signature(self, time_signature: ET.Element) -> AST.TimeSignature:
        time_symbol: Optional[AST.Token] = None
        compound_time_signature: Optional[
            List[Union[AST.TimesigFraction, AST.Token]]
        ] = None
        time_value: Fraction = Fraction(0, 1)

        current_fraction: AST.TimesigFraction | None = None
        for child in time_signature:
            if child.tag == "numerator":
                numerator = self._visit_numerator(child)

                if current_fraction is None:
                    current_fraction = AST.TimesigFraction(numerator, None)
                    compound_time_signature = [current_fraction]
                else:
                    current_fraction = AST.TimesigFraction(numerator, None)
                    if compound_time_signature is not None:
                        compound_time_signature.append(current_fraction)
                    else:
                        raise ValueError(
                            "A fraction has somehow gone outside of its scope"
                        )

            elif child.tag == "denominator":
                denominator = self._visit_denominator(child)
                if current_fraction is None:
                    raise ValueError("There should be a fraction for a denominator")
                current_fraction.denominator = denominator
            elif child.tag == "timesig":
                time_symbol = self._visit_token(child)
            elif child.tag in {"plus", "time_relation"}:
                token = self._visit_token(child)
                if current_fraction is None:
                    raise ValueError("No available fraction but time relation found")
                if compound_time_signature is None:
                    raise ValueError("Plus without compound time signature open")
                compound_time_signature.append(current_fraction)
                current_fraction = None
                compound_time_signature.append(token)

        if compound_time_signature is not None:
            time_value = (
                sum(
                    [
                        x.value()
                        for x in compound_time_signature
                        if isinstance(x, AST.TimesigFraction)
                    ],
                    start=Fraction(0),
                )
                * 4
            )  # To adjust it to the duration of the beat
        elif time_symbol is not None:
            time_value = MS.SYMBOL_TIMESIG_DUR[time_symbol.modifiers["type"]]
        else:
            raise ValueError("No value for time information")

        return AST.TimeSignature(time_symbol, compound_time_signature, time_value)

    def _visit_denominator(self, denominator: ET.Element) -> AST.Denominator:
        digits: List[AST.Token] = []

        for num in denominator:
            digits.append(self._visit_token(num))

        number = AST.Number(digits)
        return AST.Denominator(number)

    def _visit_numerator(self, numerator: ET.Element) -> AST.Numerator:
        processed: List[Union[AST.Number, AST.Token]] = []
        current_num: List[AST.Token] = []

        for child in numerator:
            token = self._visit_token(child)

            if token.token_type == TT.TokenType.NUMBER:
                current_num.append(token)
            elif token.token_type == TT.TokenType.PLUS:
                if len(current_num) == 0:
                    raise ValueError("Plus sign without any digits in the numerator")
                processed.append(AST.Number(current_num))
                current_num = []
                processed.append(token)

        if len(current_num) != 0:
            processed.append(AST.Number(current_num))

        return AST.Numerator(processed)

    def _visit_tuplet(self, tuplet: ET.Element) -> AST.Tuplet:
        tuplet_tok: Optional[AST.Token] = None
        digits: List[AST.Token] = []

        for child in tuplet:
            if child.tag == "tuplet":
                tuplet_tok = self._visit_token(child)
            elif child.tag == "number":
                digits.append(self._visit_token(child))

        if tuplet_tok is None:
            raise ValueError("No tuplet token under tuplet node.")
        tuplet_tok = cast(AST.Token, tuplet_tok)
        return AST.Tuplet(AST.Number(digits) if len(digits) > 0 else None, tuplet_tok)

    def _visit_token(self, token: ET.Element) -> AST.Token:
        token_type = TT.TokenType(token.tag)
        modifiers: Dict[str, Any] = {}

        staff = maybe(token.get("staff", None), int)
        position = maybe(token.get("position", None), int)
        ident = maybe(token.get("id", None), int)

        if ident is None:
            raise ValueError("Token has no identifier")

        if token_type in CLASS_TYPE and CLASS_TYPE[token_type] == TT.Digits:
            mod = TT.Digits(maybe(token.get("type"), int))
        else:
            try:
                # FIXME: This potentially allows the string to escape without conversion
                mod = maybe(token.get("type"), CLASS_TYPE[token_type])
            except KeyError:
                mod = None

        if mod is not None:
            modifiers["type"] = mod

        if token_type == TT.TokenType.CLEF:
            octave = token.get("oct")
            if octave is not None:
                modifiers["oct"] = int(octave)
        if token_type == TT.TokenType.NOTEHEAD:
            if "grace" in token.attrib:
                modifiers["grace"] = bool(token.attrib["grace"])
            if "cue" in token.attrib:
                modifiers["cue"] = bool(token.attrib["cue"])
        return AST.Token(
            token_type, modifiers, MS.StaffPosition(staff, position), ident
        )

    @staticmethod
    def _get_delta(node: ET.Element) -> Fraction:
        delta = node.get("delta")
        if delta is None:
            raise ValueError("Compulsory Delta value was not found")
        return Fraction(*map(int, delta.split("/")))

    @staticmethod
    def _get_staff(node: ET.Element) -> int:
        staff = node.get("staff")
        if staff is None:
            raise ValueError("Compulsory staff value was not found")
        return int(staff)

    @staticmethod
    def _get_position(node: ET.Element) -> int:
        position = node.get("position")
        if position is None:
            raise ValueError("Compulsory position value was not found")
        return int(position)

    @staticmethod
    def _get_fifths(node: ET.Element) -> Optional[int]:
        return maybe(node.get("fifths"), int)

    def reset(self) -> None:
        """Reset object to its default state."""
        pass


T1 = TypeVar("T1")
T2 = TypeVar("T2")


def maybe(obj: T1 | None, func: Callable[[T1], T2]) -> T2 | None:
    """I am tired of writing if shit is not None."""
    if obj is not None:
        return func(obj)
    return None
