# The CWMN Optical Music Recognition Framework (COMREF) toolset.
#
# Copyright (C) 2025, Pau Torras <ptorras@cvc.uab.cat>
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
Convert MTN AST into Arnau Baro string format.
"""

from fractions import Fraction
from typing import Dict, List, Tuple

from .mtn import MS, TT
from .mtn import ast as AST

EPSILON = "epsilon"


FLAGSBEAMS2NTYPE = {
    1: "8th",
    2: "16th",
    3: "32nd",
    4: "64th",
}

REST2NTYPE = {
    TT.NoteType.NT_HALF: "half",
    TT.NoteType.NT_QUARTER: "quarter",
    TT.NoteType.NT_EIGHTH: "eighth",
    TT.NoteType.NT_16TH: "16th",
    TT.NoteType.NT_32ND: "32th",
    TT.NoteType.NT_64TH: "64th",
    TT.NoteType.NT_BREVE: "breve",
    TT.NoteType.NT_LONG: "long",
}

ACCID2STR = {
    TT.AccidentalType.ACC_SHARP: "sharp",
    TT.AccidentalType.ACC_FLAT: "flat",
    TT.AccidentalType.ACC_NATURAL: "natural",
    TT.AccidentalType.ACC_DOUBLE_FLAT: "doubleFlat",
    TT.AccidentalType.ACC_DOUBLE_SHARP: "doubleSharp",
}

BARLINE2STRING = {
    TT.BarlineType.BL_DASHED: "dashed",
    TT.BarlineType.BL_HEAVY: "heavy",
    TT.BarlineType.BL_REGULAR: "light",
}

REPEAT2STRING = {
    TT.StartStop.START: "repeat",
    TT.StartStop.STOP: "repeat",
}

BARLINE_COMPONENT = {
    TT.TokenType.BARLINE: BARLINE2STRING,
    TT.TokenType.REPEAT: REPEAT2STRING,
}


class ABaroExportError(ValueError):
    ...


class VisitorToABaro(AST.Visitor):
    """Convert tree into Arnau Baro's OMR format."""

    def __init__(self) -> None:
        super().__init__()

        self.beam_stack = 0
        self.flag_stack = 0
        self.last_time = -Fraction(1)

    def visit_ast(self, root: AST.SyntaxNode) -> Dict[Tuple[str, str], str]:
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

    def visit_score(self, score: AST.Score) -> Dict[Tuple[str, str], List[str]]:
        """Perform visiting operation on Score node."""
        output = {}
        for measure in score.measures:
            output[(measure.part_id, measure.measure_id)] = measure.accept(self)

        return output

    def visit_measure(self, measure: AST.Measure) -> List[str]:
        """Perform visiting operation on Measure node."""
        output = []
        self.last_time = -Fraction(1)

        if measure.staves > 1:
            raise ABaroExportError("ABaro exporter supports only single-staff works")

        if measure.left_barline is not None:
            output.extend(measure.left_barline.accept(self))

        for child in measure.elements:
            output.extend(child.accept(self))

        if measure.right_barline is not None:
            output.extend(measure.right_barline.accept(self))

        if output[-1] == EPSILON:
            output = output[:-1]

        return output

    def visit_toplevel(self, toplevel: AST.TopLevel) -> List[str]:
        """Perform visiting operation on TopLevel node."""
        raise NotImplementedError("This method should not be called on ABaro exporter")

    def visit_note(self, note: AST.Note) -> List[str]:
        """Perform visiting operation on Note node."""
        raise NotImplementedError("This method should not be called on ABaro exporter")

    def visit_token(self, token: AST.Token) -> List[str]:
        """Perform visiting operation on Token node."""
        raise NotImplementedError("This method should not be called on ABaro exporter")

    def visit_chord(self, chord: AST.Chord) -> List[str]:
        """Perform visiting operation on Chord node."""

        # Grace notes count to a time increment of zero, so they can be accepted.
        if self.last_time > chord.delta:
            raise ABaroExportError("ABaro exporter supports only homophonic works")
        self.last_time = chord.delta

        output = []

        # Accidentals must go on the preceeding epsilon of the notes they alter.
        if any([len(x.accidentals) > 0 for x in chord.notes]):
            for note in chord.notes:
                for accidental in note.accidentals:
                    output.append(
                        self._generate_accidental(
                            accidental,
                            note.notehead.position,
                        )
                    )
            output.append(EPSILON)

        # Starting slurs come before the notehead they alter and ending slurs after.
        if any(
            [
                not isinstance(x, AST.Tuplet)
                and x.token_type == TT.TokenType.SLUR
                and x.modifiers["type"] == TT.StartStop.START
                for note in chord.notes
                for x in note.modifiers
            ]
        ):
            output.extend(["startSlur.noNote", EPSILON])

        # In ABaro notation, the stem direction determines the order of the elements of
        # the chord. If the stem goes upward, the stem precedes the notes, as in
        # top-down order. Otherwise, it goes afterwards.

        if chord.stem is not None and chord.is_stem_upwards():
            output.append(self._generate_appendage(chord))

        for note in chord.notes:
            output.append(self._generate_notehead(note.notehead, chord))

        if chord.stem is not None and not chord.is_stem_upwards():
            output.append(self._generate_appendage(chord))

        output.append(EPSILON)

        # Ending slurs come afterward
        if any(
            [
                not isinstance(x, AST.Tuplet)
                and x.token_type == TT.TokenType.SLUR
                and x.modifiers["type"] == TT.StartStop.STOP
                for note in chord.notes
                for x in note.modifiers
            ]
        ):
            output.extend(["endSlur.noNote", EPSILON])

        # Dots on the other hand go afterward. Their position is indeterminate.
        if any([len(x.dots) > 0 for x in chord.notes]):
            for note in chord.notes:
                for _ in note.dots:
                    output.append("dot.noNote")
            output.append(EPSILON)

        return output

    def _pitch2line(self, pos: MS.StaffPosition) -> str:
        if pos.position is None:
            return "noNote"
        p = pos.position
        return f"{'L' if p % 2 == 0 else 'S'}{p // 2}"

    def _generate_appendage(self, chord: AST.Chord) -> str:
        if chord.stem is None:
            raise ABaroExportError("Generate appendage called on chord w/o stem")
        stem = chord.stem
        direction = "Up" if stem.modifiers["type"] == TT.StemDirection.UP else "Down"

        if self.flag_stack == 0 and self.beam_stack == 0:
            return self._generate_stem(direction)
        elif self.flag_stack == 0 and self.beam_stack > 0:
            return self._generate_beam(direction)
        elif self.flag_stack > 0 and self.beam_stack == 0:
            return self._generate_flag(direction)
        else:
            raise ABaroExportError("Invalid flag/beam state")

    def _generate_stem(self, direction: str) -> str:
        return f"steamQuarterHalf{direction}.noNote"

    def _generate_beam(self, direction: str) -> str:
        return f"beam{FLAGSBEAMS2NTYPE[self.beam_stack]}{direction}.noNote"

    def _generate_flag(self, direction: str) -> str:
        return f"flag{FLAGSBEAMS2NTYPE[self.flag_stack]}{direction}.noNote"

    def _generate_accidental(
        self,
        accidental: AST.Token,
        position: MS.StaffPosition,
    ) -> str:
        accid = ACCID2STR[accidental.modifiers["type"]]
        pos = self._pitch2line(position)
        return f"{accid}.{pos}"

    def _generate_notehead(self, notehead: AST.Token, chord: AST.Chord) -> str:
        nhtype = notehead.modifiers["type"]
        if nhtype == TT.NoteheadType.NH_BLACK:
            nhead = "Black"
        elif nhtype == TT.NoteheadType.NH_SLASH:
            nhead = "Slash"
        elif nhtype == TT.NoteheadType.NH_WHITE and chord.stem is None:
            nhead = "Whole"
        elif nhtype == TT.NoteheadType.NH_WHITE and chord.stem is not None:
            nhead = "Half"
        else:
            raise ABaroExportError("Notehead type is not supported")
        pos = self._pitch2line(notehead.position)
        return f"notehead{nhead}.{pos}"

    def visit_rest(self, rest: AST.Rest) -> List[str]:
        """Perform visiting operation on Rest node."""
        output = []

        rest_token = f"{REST2NTYPE[rest.rest_token.modifiers['type']]}Rest.noNote"
        output.extend([rest_token, EPSILON])

        # Dots again go afterward.
        if len(rest.dots) > 0:
            for _ in rest.dots:
                output.extend(["dot.noNote"])
            output.append(EPSILON)

        return output

    def visit_note_group(self, note_group: AST.NoteGroup) -> List[str]:
        """Perform visiting operation on NoteGroup node."""
        output = []

        flags = len(
            [x for x in note_group.appendages if x.token_type == TT.TokenType.FLAG]
        )
        beams = len(
            [x for x in note_group.appendages if x.token_type == TT.TokenType.BEAM]
        )

        if self.beam_stack == 0 and beams > 0:
            first_chord = note_group.get_first_chord()
            output.extend(
                [
                    f"beam{'Up' if first_chord.is_stem_upwards() else 'Down'}Start",
                    EPSILON,
                ]
            )

        self.flag_stack += flags
        self.beam_stack += beams

        if self.beam_stack != 0 and self.flag_stack != 0:
            raise ABaroExportError(
                "Current AST contains both beams and flags on the same group"
            )

        # Arching elements between chords must be added as an individual element after
        # an epsilon (beams basically)
        for subgroup in note_group.children:
            output.extend(subgroup.accept(self))

        self.flag_stack -= flags
        self.beam_stack -= beams

        if self.beam_stack == 0 and beams > 0:
            first_chord = note_group.get_first_chord()
            output.extend(
                [
                    f"beam{'Up' if first_chord.is_stem_upwards() else 'Down'}End",
                    EPSILON,
                ]
            )

        return output

    def visit_attributes(self, attributes: AST.Attributes) -> List[str]:
        """Perform visiting operation on Attributes node."""
        output = []

        if (
            len(attributes.clef) > 1
            or len(attributes.key) > 1
            or len(attributes.timesig) > 1
        ):
            raise ABaroExportError("ABaro exporter supports only single-staff works")

        clef = next(iter(attributes.clef.values()))
        key = next(iter(attributes.key.values()))
        timesig = next(iter(attributes.timesig.values()))

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

        time_symbol = time_signature.time_symbol
        time_fraction = time_signature.compound_time_signature

        if time_symbol is not None:
            output.extend(
                [
                    self._generate_time_symbol(time_symbol),
                    EPSILON,
                ]
            )

        elif time_fraction is not None:
            if len(time_fraction) == 1 and isinstance(
                time_fraction[0], AST.TimesigFraction
            ):
                output.extend(time_fraction[0].accept(self))
            else:
                raise ABaroExportError("Unsupported time signature")
        else:
            return []
        return output

    def _generate_time_symbol(self, time_symbol: AST.Token) -> str:
        variant = time_symbol.modifiers["type"]
        if variant == TT.TimeSymbol.TS_COMMON:
            return "timeSig_common.noNote"
        elif variant == TT.TimeSymbol.TS_CUT:
            return "timeSig_cut.noNote"
        raise ABaroExportError(f"Unsupported time symbol: {variant}")

    def visit_key(self, key: AST.Key) -> List[str]:
        """Perform visiting operation on Key node."""
        output = []
        processed = False

        for accidental in key.naturals + key.accidentals:
            output.append(self._generate_accidental(accidental, accidental.position))
            processed = True
        if processed:
            output.append(EPSILON)

        return output

    def visit_clef(self, clef: AST.Clef) -> List[str]:
        """Perform visiting operation on Clef node."""
        if clef.clef_token is None:
            return []
        return [f"{clef.sign.name}-Clef.{self._pitch2line(clef.position)}", EPSILON]

    def visit_direction(self, direction: AST.Direction) -> List[str]:
        """Perform visiting operation on Direction node."""
        return []

    def visit_barline(self, barline: AST.Barline) -> List[str]:
        """Perform visiting operation on Barline node."""
        barline_components = "-".join(
            [
                BARLINE_COMPONENT[x.token_type][x.modifiers["type"]]
                for x in barline.barline_tokens
            ]
        )

        return [f"barline_{barline_components}.noNote", EPSILON]

    def visit_tuplet(self, tuplet: AST.Tuplet) -> List[str]:
        """Perform visiting operation on Tuplet node."""
        raise NotImplementedError("This method should not be called on ABaro exporter")

    def visit_numerator(self, numerator: AST.Numerator) -> List[str]:
        """Perform visiting operation on Numerator node."""
        raise NotImplementedError("This method should not be called on ABaro exporter")

    def visit_denominator(self, denominator: AST.Denominator) -> List[str]:
        """Perform visiting operation on Denominator node."""
        raise NotImplementedError("This method should not be called on ABaro exporter")

    def visit_number(self, number: AST.Number) -> List[str]:
        """Perform visiting operation on Number node."""
        raise NotImplementedError("This method should not be called on ABaro exporter")

    def visit_timesig_fraction(self, fraction: AST.TimesigFraction) -> List[str]:
        """Perform visiting operation on timesig fraction node."""
        numerator = fraction.numerator.value()
        denominator = (
            fraction.denominator.value() if fraction.denominator is not None else 1
        )

        return [f"timeSig_{numerator}-{denominator}.noNote", EPSILON]
