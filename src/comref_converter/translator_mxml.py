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
Conversor from MusicXML to MTN.
"""

from copy import deepcopy
from decimal import Decimal
from fractions import Fraction
from typing import Any, Dict, List, Optional, Set, Tuple, TypeVar, Union, cast
from xml.etree import ElementTree as ET

from . import mtn as MTN
from . import music_state as MST
from . import mxml as MXML
from . import symbol_table as ST
from .group_stack import GroupStack
from .translator_base import MeasureID, Translator
from .visitor_get_tokens import VisitorGetTokens

CueGrace = Tuple[bool, bool]


# The idea of this is keeping track of what can and cannot be converted back and forth
# and their equivalence between notations.

NTYPE_MXML2MTN: Dict[MXML.TT.NoteTypeValue, MTN.TT.NoteType] = {
    MXML.TT.NoteTypeValue.MAXIMA: MTN.TT.NoteType.NT_MAXIMA,
    MXML.TT.NoteTypeValue.LONG: MTN.TT.NoteType.NT_LONG,
    MXML.TT.NoteTypeValue.BREVE: MTN.TT.NoteType.NT_BREVE,
    MXML.TT.NoteTypeValue.WHOLE: MTN.TT.NoteType.NT_WHOLE,
    MXML.TT.NoteTypeValue.HALF: MTN.TT.NoteType.NT_HALF,
    MXML.TT.NoteTypeValue.QUARTER: MTN.TT.NoteType.NT_QUARTER,
    MXML.TT.NoteTypeValue.EIGHTH: MTN.TT.NoteType.NT_EIGHTH,
    MXML.TT.NoteTypeValue.VALUE_16TH: MTN.TT.NoteType.NT_16TH,
    MXML.TT.NoteTypeValue.VALUE_32ND: MTN.TT.NoteType.NT_32ND,
    MXML.TT.NoteTypeValue.VALUE_64TH: MTN.TT.NoteType.NT_64TH,
    MXML.TT.NoteTypeValue.VALUE_128TH: MTN.TT.NoteType.NT_128TH,
    MXML.TT.NoteTypeValue.VALUE_256TH: MTN.TT.NoteType.NT_256TH,
    MXML.TT.NoteTypeValue.VALUE_512TH: MTN.TT.NoteType.NT_512TH,
    MXML.TT.NoteTypeValue.VALUE_1024TH: MTN.TT.NoteType.NT_1024TH,
}

TIED_TYPE_MXML2MTN: Dict[MXML.TT.TiedType, MTN.TT.StartStop] = {
    MXML.TT.TiedType.START: MTN.TT.StartStop.START,
    MXML.TT.TiedType.STOP: MTN.TT.StartStop.STOP,
}

STARTSTOP_MXML2MTN: Dict[MXML.TT.StartStop, MTN.TT.StartStop] = {
    MXML.TT.StartStop.START: MTN.TT.StartStop.START,
    MXML.TT.StartStop.STOP: MTN.TT.StartStop.STOP,
}

ACCIDENTAL_MXML2MTN: Dict[MXML.TT.AccidentalValue, MTN.TT.AccidentalType] = {
    MXML.TT.AccidentalValue.SHARP: MTN.TT.AccidentalType.ACC_SHARP,
    MXML.TT.AccidentalValue.NATURAL: MTN.TT.AccidentalType.ACC_NATURAL,
    MXML.TT.AccidentalValue.FLAT: MTN.TT.AccidentalType.ACC_FLAT,
    MXML.TT.AccidentalValue.DOUBLE_SHARP: MTN.TT.AccidentalType.ACC_DOUBLE_SHARP,
    MXML.TT.AccidentalValue.FLAT_FLAT: MTN.TT.AccidentalType.ACC_DOUBLE_FLAT,
    MXML.TT.AccidentalValue.QUARTER_FLAT: MTN.TT.AccidentalType.ACC_QUARTER_FLAT,
    MXML.TT.AccidentalValue.QUARTER_SHARP: MTN.TT.AccidentalType.ACC_QUARTER_SHARP,
}

NHEAD_MXML2MTN: Dict[MXML.TT.NoteheadValue, MTN.TT.NoteheadType] = {
    MXML.TT.NoteheadValue.X: MTN.TT.NoteheadType.NH_CROSS,
    MXML.TT.NoteheadValue.CROSS: MTN.TT.NoteheadType.NH_CROSS,
    MXML.TT.NoteheadValue.DIAMOND: MTN.TT.NoteheadType.NH_DIAMOND,
    MXML.TT.NoteheadValue.TRIANGLE: MTN.TT.NoteheadType.NH_TRIANGLE,
    MXML.TT.NoteheadValue.INVERTED_TRIANGLE: MTN.TT.NoteheadType.NH_INVERTED_TRIANGLE,
}

STEM_MXML2MTN: Dict[MXML.TT.StemValue, MTN.TT.StemDirection] = {
    MXML.TT.StemValue.UP: MTN.TT.StemDirection.UP,
    MXML.TT.StemValue.DOWN: MTN.TT.StemDirection.DOWN,
}

SIGN_MXML2MTN: Dict[MXML.TT.ClefSign, MTN.TT.NamedPitch] = {
    MXML.TT.ClefSign.G: MTN.TT.NamedPitch.G,
    MXML.TT.ClefSign.C: MTN.TT.NamedPitch.C,
    MXML.TT.ClefSign.F: MTN.TT.NamedPitch.F,
}

PITCH_MXML2MTN: Dict[MXML.TT.Step, MTN.TT.NamedPitch] = {
    MXML.TT.Step.A: MTN.TT.NamedPitch.A,
    MXML.TT.Step.B: MTN.TT.NamedPitch.B,
    MXML.TT.Step.C: MTN.TT.NamedPitch.C,
    MXML.TT.Step.D: MTN.TT.NamedPitch.D,
    MXML.TT.Step.E: MTN.TT.NamedPitch.E,
    MXML.TT.Step.F: MTN.TT.NamedPitch.F,
    MXML.TT.Step.G: MTN.TT.NamedPitch.G,
}

BAR_STYLE_MXML2MTN: Dict[MXML.TT.BarStyle, List[MTN.TT.BarlineType]] = {
    MXML.TT.BarStyle.REGULAR: [MTN.TT.BarlineType.BL_REGULAR],
    MXML.TT.BarStyle.DOTTED: [MTN.TT.BarlineType.BL_DOTTED],
    MXML.TT.BarStyle.DASHED: [MTN.TT.BarlineType.BL_DASHED],
    MXML.TT.BarStyle.HEAVY: [MTN.TT.BarlineType.BL_HEAVY],
    MXML.TT.BarStyle.TICK: [MTN.TT.BarlineType.BL_TICK],
    MXML.TT.BarStyle.SHORT: [MTN.TT.BarlineType.BL_SHORT],
    MXML.TT.BarStyle.HEAVY_HEAVY: [
        MTN.TT.BarlineType.BL_HEAVY,
        MTN.TT.BarlineType.BL_HEAVY,
    ],
    MXML.TT.BarStyle.HEAVY_LIGHT: [
        MTN.TT.BarlineType.BL_HEAVY,
        MTN.TT.BarlineType.BL_REGULAR,
    ],
    MXML.TT.BarStyle.LIGHT_LIGHT: [
        MTN.TT.BarlineType.BL_REGULAR,
        MTN.TT.BarlineType.BL_REGULAR,
    ],
    MXML.TT.BarStyle.LIGHT_HEAVY: [
        MTN.TT.BarlineType.BL_REGULAR,
        MTN.TT.BarlineType.BL_HEAVY,
    ],
}

CLEF_MXML2MTN: Dict[MXML.TT.ClefSign, MTN.TT.ClefType] = {
    MXML.TT.ClefSign.G: MTN.TT.ClefType.CLEF_G,
    MXML.TT.ClefSign.F: MTN.TT.ClefType.CLEF_F,
    MXML.TT.ClefSign.C: MTN.TT.ClefType.CLEF_C,
    MXML.TT.ClefSign.PERCUSSION: MTN.TT.ClefType.CLEF_PERCUSSION,
}

# Decide which point-to-point token to use
P2P_TOKENS: Dict[str, MTN.TT.TokenType] = {
    "glissando": MTN.TT.TokenType.GLISSANDO,
    "slide": MTN.TT.TokenType.SLIDE,
    "slur": MTN.TT.TokenType.SLUR,
    "wavy-line": MTN.TT.TokenType.WAVY_LINE,
}

ORNAMENT_TOKENS: Dict[str, MTN.TT.TokenType] = {
    "trill-mark": MTN.TT.TokenType.TRILL,
    "turn": MTN.TT.TokenType.TURN,
    "wavy-line": MTN.TT.TokenType.WAVY_LINE,
    "mordent": MTN.TT.TokenType.MORDENT,
    "schleifer": MTN.TT.TokenType.SCHLEIFER,
    "haydn": MTN.TT.TokenType.HAYDN,
}

ARTICULATION_TOKENS: Dict[str, MTN.TT.TokenType] = {
    "accent": MTN.TT.TokenType.ACCENT,
    "strong-accent": MTN.TT.TokenType.ACCENT,
    "staccato": MTN.TT.TokenType.STACCATO,
    "tenuto": MTN.TT.TokenType.TENUTO,
    "staccatissimo": MTN.TT.TokenType.STACCATO,
    "caesura": MTN.TT.TokenType.CAESURA,
}

DYNAMICS_MXML2MTN: Dict[MXML.TT.DynamicsType, MTN.TT.DynamicsType] = {
    MXML.TT.DynamicsType.P: MTN.TT.DynamicsType.DYN_P,
    MXML.TT.DynamicsType.PP: MTN.TT.DynamicsType.DYN_PP,
    MXML.TT.DynamicsType.PPP: MTN.TT.DynamicsType.DYN_PPP,
    MXML.TT.DynamicsType.PPPP: MTN.TT.DynamicsType.DYN_PPPP,
    MXML.TT.DynamicsType.PPPPP: MTN.TT.DynamicsType.DYN_PPPPP,
    MXML.TT.DynamicsType.PPPPPP: MTN.TT.DynamicsType.DYN_PPPPPP,
    MXML.TT.DynamicsType.F: MTN.TT.DynamicsType.DYN_F,
    MXML.TT.DynamicsType.FF: MTN.TT.DynamicsType.DYN_FF,
    MXML.TT.DynamicsType.FFF: MTN.TT.DynamicsType.DYN_FFF,
    MXML.TT.DynamicsType.FFFF: MTN.TT.DynamicsType.DYN_FFFF,
    MXML.TT.DynamicsType.FFFFF: MTN.TT.DynamicsType.DYN_FFFFF,
    MXML.TT.DynamicsType.FFFFFF: MTN.TT.DynamicsType.DYN_FFFFFF,
    MXML.TT.DynamicsType.MP: MTN.TT.DynamicsType.DYN_MP,
    MXML.TT.DynamicsType.MF: MTN.TT.DynamicsType.DYN_MF,
    MXML.TT.DynamicsType.SF: MTN.TT.DynamicsType.DYN_SF,
    MXML.TT.DynamicsType.SFP: MTN.TT.DynamicsType.DYN_SFP,
    MXML.TT.DynamicsType.SFPP: MTN.TT.DynamicsType.DYN_SFPP,
    MXML.TT.DynamicsType.FP: MTN.TT.DynamicsType.DYN_FP,
    MXML.TT.DynamicsType.RF: MTN.TT.DynamicsType.DYN_RF,
    MXML.TT.DynamicsType.RFZ: MTN.TT.DynamicsType.DYN_RFZ,
    MXML.TT.DynamicsType.SFZ: MTN.TT.DynamicsType.DYN_SFZ,
    MXML.TT.DynamicsType.SFFZ: MTN.TT.DynamicsType.DYN_SFFZ,
    MXML.TT.DynamicsType.FZ: MTN.TT.DynamicsType.DYN_FZ,
    MXML.TT.DynamicsType.N: MTN.TT.DynamicsType.DYN_N,
    MXML.TT.DynamicsType.PF: MTN.TT.DynamicsType.DYN_PF,
    MXML.TT.DynamicsType.SFZP: MTN.TT.DynamicsType.DYN_SFZP,
}

WEDGE_MXML2MTN: Dict[MXML.TT.WedgeType, MTN.TT.WedgeType] = {
    MXML.TT.WedgeType.CRESCENDO: MTN.TT.WedgeType.WEDGE_CRESCENDO,
    MXML.TT.WedgeType.DIMINUENDO: MTN.TT.WedgeType.WEDGE_DIMINUENDO,
    MXML.TT.WedgeType.STOP: MTN.TT.WedgeType.WEDGE_STOP,
}

BWFW_MXML2MTN: Dict[MXML.TT.BackwardForward, MTN.TT.BackwardForward] = {
    MXML.TT.BackwardForward.BACKWARD: MTN.TT.BackwardForward.DIR_BACKWARD,
    MXML.TT.BackwardForward.FORWARD: MTN.TT.BackwardForward.DIR_FORWARD,
}

BEAM_PRECEDENCE: Dict[MXML.TT.BeamValue, int] = {
    MXML.TT.BeamValue.BEGIN: 0,
    MXML.TT.BeamValue.CONTINUE: 1,
    MXML.TT.BeamValue.END: 4,
    MXML.TT.BeamValue.FORWARD_HOOK: 2,
    MXML.TT.BeamValue.BACKWARD_HOOK: 3,
}


def _maybe_int(x: Optional[str]) -> Optional[int]:
    if x is not None:
        return int(x)
    return None


SyntaxNodeSubtype = TypeVar("SyntaxNodeSubtype", bound=MTN.AST.SyntaxNode)


class UnsupportedElement(ValueError):
    """Exception to throw with (currently) unsupported elements."""


class TranslatorMXML(Translator):
    """Navigates a MXML file and converts it into MTN."""

    _ALL_STAVES = -1

    def __init__(self) -> None:
        self.state = MST.ScoreState()
        self.symbol_table = ST.SymbolTable()

        # Super bloated, but necessary since MXML considers each of these kinds of note
        # independent and have to be treated separately.
        # For note groups keep a stack of chords under the same starting level of beams.

        self.current_chord: Dict[bool, Optional[MTN.AST.Chord]] = {
            grace: None for grace in [False, True]
        }

        self.group_stack: GroupStack = GroupStack(self.state, self.symbol_table)
        self.last_measure: Optional[MTN.AST.Measure] = None

    def translate(
        self,
        score_in: ET.Element,
        score_id: str,
        engr_first_line: Set[MeasureID],
    ) -> MTN.AST.Score:
        """Translate a MusicXML score-partwise root element into MTN.

        Parameters
        ----------
        score_in : ET.Element
            The score-partwise element of a MusicXML document.
        engr_first_line : Set[MeasureID]
            Set of measure identifiers for those systems that lie at the beginning of a
            line (and thus need a refresh of clef and key elements).

        Returns
        -------
        MTN.AST.Score
            Representation of the score in MTN.
        """
        output = MTN.AST.Score([], score_id=score_id)
        for child in score_in:
            if child.tag == "part":
                part_dict = self._visit_part(child, engr_first_line)
                for measure in part_dict.values():
                    output.measures.append(measure)
                self.symbol_table.reset()
        return output

    def reset(self) -> None:
        """Reset object to its default state."""
        self.state = MST.ScoreState()
        self.symbol_table = ST.SymbolTable()

        self.group_stack.reset()
        self.current_chord = {grace: None for grace in [False, True]}
        self.last_measure = None

    def _duplicate_subtree(
        self,
        obj: SyntaxNodeSubtype,
    ) -> SyntaxNodeSubtype:
        subtree = deepcopy(obj)

        token_visitor = VisitorGetTokens()
        tokens = token_visitor.visit_ast(subtree)
        for token in tokens:
            token.token_id = self.symbol_table.give_identifier()
        return subtree

    def _new_measure(self) -> None:
        # print("NEW MEASURE", end="\n\n")
        self.state.new_measure()

        # Soooo... apparently musicXML allows beams going from measure to measure...
        # self.group_stack.reset()
        self.current_chord = {grace: None for grace in [False, True]}

    def _new_part(self) -> None:
        self.state = MST.ScoreState()
        self.current_chord = {grace: None for grace in [False, True]}
        self.group_stack.reset()
        self.last_measure = None

    def _visit_part(
        self,
        part_element: ET.Element,
        engr_first_line: Set[MeasureID],
    ) -> Dict[MeasureID, MTN.AST.Measure]:
        """Visit a part element and produce a sequence of MTN measures.

        Parameters
        ----------
        part_element : ET.Element
            The part element to visit.
        engr_first_line : Set[MeasureID]
            Set of measure identifiers for those systems that lie at the beginning of a
            line (and thus need a refresh of clef and key elements).

        Returns
        -------
        Dict[MeasureID, MTN.AST.Measure]
            A dictionary with measure identifiers as keys and the measure converted to
            MTN as values.
        """
        part_id = part_element.get("id", None)
        output_dict: Dict[MeasureID, MTN.AST.Measure] = {}
        for measure in part_element:
            measure_id = measure.get("number", None)
            # print(f"measure id: {measure_id} !!!!!!!!!!!!!!!!!!!!!!!!")

            assert isinstance(part_id, str) and isinstance(
                measure_id, str
            ), "PartID or MeasureID could not be found"
            identifier: MeasureID = (part_id, measure_id)

            measure_mtn = self._visit_measure(measure)

            if identifier in engr_first_line:
                self._add_start_measure_elements(measure_mtn)
            measure_mtn = self._postprocess_measure(measure_mtn)

            output_dict[identifier] = measure_mtn
            measure_mtn.measure_id = measure_id
            measure_mtn.part_id = part_id

            self.last_measure = measure_mtn

            self._new_measure()

        # Check the last measure has a right barline
        if self.last_measure is not None and self.last_measure.right_barline is None:
            self.last_measure.right_barline = MTN.AST.Barline(
                delta=self.last_measure.duration,
                barline_tokens=[
                    MTN.AST.Token(
                        MTN.TT.TokenType.BARLINE,
                        {"type": MTN.TT.BarlineType.BL_REGULAR},
                        MTN.MS.StaffPosition(None, None),
                        self.symbol_table.give_identifier(),
                    )
                ],
                modifiers=[],
            )
            self.last_measure.right_barline
        self._new_part()

        return output_dict

    def _postprocess_measure(self, measure: MTN.AST.Measure) -> MTN.AST.Measure:
        """Ensure compliance to MTN spec."""
        new_children: List[MTN.AST.TopLevel] = []

        direction = None
        for child in measure.elements:
            if isinstance(child, MTN.AST.Direction):
                if direction is not None:
                    if direction.delta == child.delta:
                        direction.merge(child)
                    else:
                        new_children.append(direction)
                        new_children.append(child)
                        direction = None
                else:
                    direction = child
            else:
                if direction is not None:
                    new_children.append(direction)
                    direction = None
                if isinstance(child, MTN.AST.NoteGroup):
                    child.simplify()
                new_children.append(child)

        # Make sure no dangling direction is left.
        if direction is not None:
            new_children.append(direction)

        # Ensure barlines are properly added where necessary
        if self.last_measure is not None:
            if measure.left_barline is not None:
                # If there are two conflicting barlines, assume there is a line break
                # and continue.
                if self.last_measure.right_barline is None:
                    self.last_measure.right_barline = deepcopy(measure.left_barline)
                    self.last_measure.right_barline.delta = self.last_measure.duration
            elif self.last_measure.right_barline is not None:
                measure.left_barline = deepcopy(self.last_measure.right_barline)
                measure.left_barline.delta = Fraction(0)
            else:
                # Default barline
                default_barline = MTN.AST.Barline(
                    delta=self.last_measure.duration,
                    barline_tokens=[
                        MTN.AST.Token(
                            MTN.TT.TokenType.BARLINE,
                            {"type": MTN.TT.BarlineType.BL_REGULAR},
                            MTN.MS.StaffPosition(None, None),
                            self.symbol_table.give_identifier(),
                        )
                    ],
                    modifiers=[],
                )
                self.last_measure.right_barline = default_barline
                measure.left_barline = deepcopy(default_barline)
                measure.left_barline.delta = Fraction(0)

        measure.elements = new_children
        measure.sort()
        return measure

    def _add_start_measure_elements(self, measure: MTN.AST.Measure) -> None:
        """Add elements at the start of a line.

        For those measures that lie at the beginning of a line, add the clef, key and
        time signature objects. The parameter object gets modified.

        Parameters
        ----------
        measure : MTN.AST.Measure
            The MTN.AST node to modify with the corresponding attribute elements.
        """
        first_liner = self.state.start_attributes()
        first_liner = self._duplicate_subtree(first_liner)

        for staff, key in first_liner.key.items():
            if key is None or staff > self.state.nstaves:
                continue
            if key.fifths is not None:
                accidental = (
                    MTN.TT.AccidentalType.ACC_SHARP
                    if key.fifths > 0
                    else MTN.TT.AccidentalType.ACC_FLAT
                )
                key.accidentals = sorted(
                    self._key_accidental_tokens(key.fifths, accidental, staff),
                    key=lambda x: int(x.position),
                )
            else:
                steps: List[MTN.TT.NamedPitch] = []
                alters: List[MTN.TT.AccidentalType] = []
                for ii, alt in enumerate(key.alterations):
                    if alt is not None:
                        steps.append(MTN.TT.NamedPitch(ii))
                        alters.append(alt)
                key.accidentals = sorted(
                    self._key_alter_tokens(steps, alters, staff),
                    key=lambda x: int(x.position),
                    reverse=True,
                )
        if len(measure.elements) and isinstance(
            measure.elements[0], MTN.AST.Attributes
        ):
            measure.elements[0].merge(first_liner)
        else:
            measure.elements.insert(0, first_liner)

    def _visit_measure(
        self,
        measure: ET.Element,
    ) -> MTN.AST.Measure:
        """Visit a measure element and produce a single Measure MTN object.

        Parameters
        ----------
        measure : ET.Element
            A MXML measure element.

        Returns
        -------
        MTN.AST.Measure
            The translation of the measure into MTN.
        """
        measure_subelements: List[MTN.AST.TopLevel] = []
        left_barline: Optional[MTN.AST.Barline] = None
        right_barline: Optional[MTN.AST.Barline] = None

        # This sets up the state and parses all attribute elements
        measure_subelements.extend(self._preparse_measure(measure))

        for child in measure:
            if child.tag == "note":
                note_out = self._visit_note(child)
                if note_out is not None:
                    measure_subelements.append(note_out)
            elif child.tag == "backup":
                self._backup_or_forward(False, child)
            elif child.tag == "forward":
                self._backup_or_forward(True, child)
            elif child.tag == "direction":
                direction = self._visit_direction(child)
                if direction is not None:
                    measure_subelements.append(direction)
            # elif child.tag == "attributes":
            #     measure_subelements.append(self._visit_attributes(child))
            elif child.tag == "barline":
                barline = self._visit_barline(child)
                if barline is None:
                    continue
                if barline.delta == 0:
                    left_barline = barline
                elif (
                    self.state.attributes.timesig[1] is not None
                    and barline.delta == self.state.attributes.timesig[1].time_value
                ):
                    right_barline = barline
                else:
                    measure_subelements.append(barline)

        output = MTN.AST.Measure(
            measure_subelements,
            left_barline,
            right_barline,
            staves=self.state.nstaves,
            measure_id="<INVALID>",
            part_id="<INVALID>",
            duration=self.state.get_duration(),
        )
        output.sort()

        return output

    def _preparse_measure(self, measure: ET.Element) -> List[MTN.AST.Attributes]:
        attribute_nodes: List[MTN.AST.Attributes] = []
        for child in measure:
            if child.tag == "note":
                self._preparse_note(child)
            elif child.tag == "backup":
                self._backup_or_forward(False, child)
            elif child.tag == "forward":
                self._backup_or_forward(True, child)
            elif child.tag == "attributes":
                attribute_nodes.append(self._visit_attributes(child))

        self.state.change_time(Fraction(0))

        return self.state.attribute_list
        # return attribute_nodes

    def _preparse_note(self, note: ET.Element) -> None:
        is_chord = note.find("chord")
        duration_element = note.find("duration")
        if is_chord is not None or duration_element is None:
            return None

        duration = self._visit_duration(duration_element)
        self.state.set_buffer(duration)
        self.state.move_buffer()

    def _backup_or_forward(
        self,
        forward: bool,
        element: ET.Element,
    ) -> None:
        value_element = element[0]
        assert (
            value_element is not None and value_element.text is not None
        ), "Empty or invalid backup element"

        value = int(value_element.text)
        increment = Fraction(value, self.state.divisions)
        if not forward:
            increment *= -1
        self.state.increment_time(increment)

    def _visit_note(
        self,
        note: ET.Element,
    ) -> Optional[Union[MTN.AST.Rest, MTN.AST.NoteGroup]]:
        """Produce a note group or a rest depending on the passed note element.

        If the note or rest begins a new group, this method will return a reference to
        the newly created object and will populate the self.current_group reference with
        it as well. If the method returns None it is updating the already created
        objects pointed at through self or it has found a note that is not to be
        displayed.

        Parameters
        ----------
        note : ET.Element
            A MXML note node.

        Returns
        -------
        Optional[Union[MTN.AST.Rest, MTN.AST.NoteGroup]]
            A Rest or NoteGroup object if a new instance of either is being created.
            None if an existing instance is being populated or if the element is not to
            be displayed.
        """
        cue: bool = False
        grace: bool = False
        rest: bool = False
        chord: bool = False
        staff: int = 1
        accidentals: List[MTN.AST.Token] = []
        beam_elements: List[ET.Element] = []
        dots: List[MTN.AST.Token] = []
        duration: Fraction = Fraction(0)
        implicit_ntype: Optional[MTN.TT.NoteType] = None
        notations: List[MTN.AST.Token | MTN.AST.Tuplet] = []
        notations_elements: List[ET.Element] = []
        ntype: Optional[MTN.TT.NoteType] = None
        pitch: Optional[MTN.MS.NotePitch] = None
        position: Optional[MTN.MS.StaffPosition] = None
        time_mod: Optional[Fraction] = None

        visible_elm = note.get("print-object", "yes")
        visible = visible_elm == "yes"

        stem: Optional[MTN.AST.Token] = None
        notehead: Optional[MTN.AST.Token] = None

        for child in note:
            if child.tag == "grace":
                grace = True
            elif child.tag == "cue":
                cue = True
            elif child.tag == "pitch":
                pitch = self._visit_pitch(child)
            elif child.tag == "unpitched":
                pitch = self._visit_unpitched(child)
            elif child.tag == "rest":
                rest = True
            elif child.tag == "chord":
                chord = True
            elif child.tag == "duration":
                duration = self._visit_duration(child)
            elif child.tag == "type":
                ntype = self._visit_type(child)
            elif child.tag == "dot":
                dots.append(self._visit_dot())
            elif child.tag == "accidental":
                accidentals = self._visit_accidental(child)
            elif child.tag == "stem":
                stem = self._visit_stem(child)
            elif child.tag == "notehead":
                notehead, valid = self._visit_notehead(child)
                if not valid:
                    visible = False
            elif child.tag == "staff":
                assert child.text is not None, "Invalid staff value"
                staff = int(child.text)
            elif child.tag == "beam":
                beam_elements.append(child)
            elif child.tag == "notations":
                notations_elements.append(child)
            elif child.tag == "time-modification":
                time_mod, implicit_ntype = self._visit_time_mod(child)

        # Get position property for the note
        position = self._get_object_position_from_pitch(staff, pitch)

        if stem is not None:
            stem.position = MTN.MS.StaffPosition(None, None)

        # Not really necessary - parent note node already has this information
        # for acc in accidentals:
        #     acc.position = position

        # for dot in dots:
        #     dot.position = position

        # Ensure the type of the object is known
        if ntype is None:
            if implicit_ntype is not None:
                ntype = implicit_ntype
            else:
                ntype = self._infer_ntype(
                    duration,
                    len(dots),
                    stem is not None,
                    grace,
                    notehead,
                    len(beam_elements),
                    time_mod,
                )

        # Get the notations tokens once the position of the note is known
        notations = [
            z
            for y in [
                self._visit_notations(x, MTN.MS.StaffPosition(None, None), time_mod)
                for x in notations_elements
            ]
            for z in y
        ]
        notations.sort(
            key=lambda x: x.token_type.value if isinstance(x, MTN.AST.Token) else "a"
        )

        if rest:
            # print("processing rest")
            self.state.move_buffer()
            self.state.set_buffer(duration)
            # self.group_stack.reset_grace(grace)

            rest_token = MTN.AST.Token(
                MTN.TT.TokenType.REST,
                {"type": ntype},
                MTN.MS.StaffPosition(staff, None),
                self.symbol_table.give_identifier(),
            )

            rest_output = MTN.AST.Rest(
                self.state.current_time,
                rest_token,
                dots,
                notations,
            )

            self.state.move_buffer()

            if not visible:
                return None
            return rest_output

        # If it is a note, ensure it has a notehead and it has all proper info
        if notehead is not None:
            notehead.position = position
            if cue:
                notehead.modifiers["cue"] = True
            if grace:
                notehead.modifiers["grace"] = True
        else:
            notehead = self._infer_notehead(ntype, position, grace, cue)

        current_note = MTN.AST.Note(notehead, dots, accidentals, notations)

        # If there is a chord token then that means the ongoing chord element should
        # be populated
        if chord:
            if not visible:
                return None
            current_chord = self.current_chord[grace]
            assert current_chord is not None, "Chord element without an active chord."

            current_chord.add_note(current_note)

            return None

        # If there is no chord element then this is the start of a new one.
        self.state.move_buffer()
        self.state.set_buffer(duration)

        # Get position property for the note again because of the potential change in
        # attributes in the music state
        position = self._get_object_position_from_pitch(staff, pitch)
        notehead.position = position

        if (
            not visible
            and len(beam_elements) == 0
            and len(notations) == 0
            and stem is None
        ):
            return None

        # Create the new chord element with the current note
        current_chord = MTN.AST.Chord(self.state.current_time, stem, [current_note])
        self.current_chord[grace] = current_chord

        # Check the beams on the stem to create corresponding NoteGroups
        if len(beam_elements) > 0:
            return_at_end = self.group_stack.bottom(grace) is None
            beam_processed = self._process_beams(beam_elements)
            # print("# # # # # " * 5)
            # print(beam_processed)
            self._create_notegroups(grace, beam_processed)
            # print({x: len(v) for x, v in self.group_stack.stack.items()})
            base_group = self.group_stack.bottom(grace)
            current_group = self.group_stack.top(grace)
            if current_group is None:
                raise ValueError("Malformed beam structure: A Group should be open")
            current_group.children.append(current_chord)
            self._remove_notegroups(grace, beam_processed)
            # print({x: len(v) for x, v in self.group_stack.stack.items()})

            if return_at_end:
                return base_group
            return None

        # Otherwise this is a singleton with flags, and these have to be created.
        # The group does not need to be stored because it will only contain a single
        # chord. It does need to be returned to add to the rest of the collection.
        flags = self._get_flags(ntype, staff)
        current_group = MTN.AST.NoteGroup(
            self.state.current_time, [current_chord], flags
        )

        return current_group

    def _get_object_position_from_pitch(
        self,
        staff: int,
        pitch: Optional[MTN.MS.NotePitch],
    ) -> MTN.MS.StaffPosition:
        current_clef = self.state.attributes.get_clef(staff)
        assert current_clef is not None, f"Invalid Clef for staff {staff}"

        # Ensure there is a position property for all elements
        if pitch is not None:
            staff_position = current_clef.pitch2pos(pitch)
            position = MTN.MS.StaffPosition(staff, staff_position)
        else:
            position = MTN.MS.StaffPosition(staff, None)

        return position

    def _get_flags(
        self,
        ntype: MTN.TT.NoteType,
        staff: int,
    ) -> List[MTN.AST.Token]:
        """Produce the flags for a specific note type object."""
        nflags = MTN.TT.NoteType.type2beams(ntype)
        if nflags is None:
            return []
        return [
            MTN.AST.Token(
                MTN.TT.TokenType.FLAG,
                {},
                MTN.MS.StaffPosition(None, None),
                self.symbol_table.give_identifier(),
            )
            for _ in range(nflags)
        ]

    def _process_beams(
        self, beams: List[ET.Element]
    ) -> List[Tuple[MXML.TT.BeamValue, Optional[int]]]:
        """Create logic representation of a beam element to ease processing."""
        beam_processed: List[Tuple[MXML.TT.BeamValue, Optional[int]]] = [
            (
                MXML.TT.BeamValue(beam.text),
                _maybe_int(beam.get("number")),
            )
            for beam in beams
        ]

        if all(map(lambda x: x[1] is not None, beam_processed)):
            beam_processed.sort(key=lambda x: x[1] or 0)
        else:
            beam_processed.sort(key=lambda x: BEAM_PRECEDENCE[x[0]])
        return beam_processed

    def _create_notegroups(
        self,
        grace: bool,
        processed_beams: List[Tuple[MXML.TT.BeamValue, Optional[int]]],
    ) -> None:
        """Create NoteGroups when necessary and add them to the stack."""
        for btype, _ in processed_beams:
            if btype in {
                MXML.TT.BeamValue.BACKWARD_HOOK,
                MXML.TT.BeamValue.FORWARD_HOOK,
                MXML.TT.BeamValue.BEGIN,
            }:
                self.group_stack.new_level(grace)

    def _remove_notegroups(
        self,
        grace: bool,
        processed_beams: List[Tuple[MXML.TT.BeamValue, Optional[int]]],
    ) -> None:
        """Remove NoteGroups from the stack."""
        for btype, _ in processed_beams:
            if btype in {
                MXML.TT.BeamValue.BACKWARD_HOOK,
                MXML.TT.BeamValue.FORWARD_HOOK,
                MXML.TT.BeamValue.END,
            }:
                self.group_stack.pop(grace)

    def _infer_ntype(
        self,
        duration: Fraction,
        dots: int,
        stem: bool,
        grace: bool,
        notehead: Optional[MTN.AST.Token],
        beams: int,
        time_mod: Optional[Fraction],
    ) -> MTN.TT.NoteType:
        """Infer the note type using the available information.

        Parameters
        ----------
        duration : Fraction
            Note duration in fractions of a quarter note.
        dots : int
            Number of dots attached to the note or object.
        stem : bool
            Whether the note has a stem attached to it or not.
        grace : bool
            Whether it is a grace note or not.
        notehead : Optional[MTN.AST.Token]
            Token for the notehead, if it exists.
        beams : Optional[int]
            Number of beams, if applicable.
        time_mod : Optional[Fraction]
            Fraction of numbers that play divided by the space they should occupy.

        Returns
        -------
        MTN.TT.NoteType
            Inferred type of the note. Defaults to quarter note if not enough info is
            available.
        """
        if beams > 0:
            return MTN.TT.NoteType.beams2type(beams)
        if notehead is not None:
            if notehead.modifiers["type"] == MTN.TT.NoteheadType.NH_WHITE:
                if stem:
                    return MTN.TT.NoteType.NT_HALF
                return MTN.TT.NoteType.NT_WHOLE

        if duration > 0:
            multiplier = Fraction(1)

            if time_mod is not None:
                multiplier *= 1 // time_mod

            if dots > 0:
                multiplier += Fraction(1, 2) * dots

            return MTN.TT.NoteType.duration2type(duration * multiplier)
        if grace:
            return MTN.TT.NoteType.NT_EIGHTH
        return MTN.TT.NoteType.NT_QUARTER

    def _infer_notehead(
        self,
        ntype: MTN.TT.NoteType,
        position: MTN.MS.StaffPosition,
        grace: bool,
        cue: bool,
    ) -> MTN.AST.Token:
        notehead_type = MTN.TT.NoteheadType.type2notehead(ntype)
        modifiers: Dict[str, Any] = {"type": notehead_type}

        # To avoid irrelevant data, include them only if needed
        if grace:
            modifiers["grace"] = True
        if cue:
            modifiers["cue"] = True

        return MTN.AST.Token(
            MTN.TT.TokenType.NOTEHEAD,
            modifiers,
            position,
            self.symbol_table.give_identifier(),
        )

    def _visit_time_mod(
        self,
        time_mod: ET.Element,
    ) -> Tuple[Fraction, Optional[MTN.TT.NoteType]]:
        """Visit time modification to obtain proper note timings.

        Parameters
        ----------
        time_mod : ET.Element
            Time modification object in the MXML tree.

        Returns
        -------
        Tuple[Fraction, Optional[MTN.TT.NoteType]]
            The number of notes that actually play in the tuplet divided by the number
            of notes that would normally play, as a Fraction. The implicit note type if
            provided in the time modification element.
        """
        actual_elm = time_mod.find("actual-notes")
        normal_elm = time_mod.find("normal-notes")
        type_elm = time_mod.find("normal-type")

        assert (
            actual_elm is not None
            and actual_elm.text is not None
            and normal_elm is not None
            and normal_elm.text is not None
        ), "Time modification without proper note indications."

        actual = int(actual_elm.text)
        normal = int(normal_elm.text)
        ntype = None
        mtn_ntype = None
        if type_elm is not None and type_elm.text is not None:
            ntype = MXML.TT.NoteTypeValue(type_elm.text)
            mtn_ntype = NTYPE_MXML2MTN[ntype]

        return (Fraction(actual, normal), mtn_ntype)

    def _visit_notations(
        self,
        notations: ET.Element,
        pitch: MTN.MS.StaffPosition,
        time_mod: Optional[Fraction],
    ) -> List[MTN.AST.Token | MTN.AST.Tuplet]:
        """Convert MXML notations element into list of MTN tokens.

        Parameters
        ----------
        notations : ET.Element
            Notations object depicting a set of notations attach to a note.
        pitch : MTN.MS.StaffPosition
            Position of the note this element is attached to.

        Returns
        -------
        List[MTN.AST.Token]
            List of converted elements into MTN.
        """
        output: List[MTN.AST.Token | MTN.AST.Tuplet] = []
        for child in notations:
            if child.tag == "tied":
                tied = self._visit_tied(child, pitch)
                if tied is not None:
                    output.append(tied)
            elif child.tag in {"slur", "glissando", "slide"}:
                ptp = self._visit_point_to_point(child, pitch)
                if ptp is not None:
                    output.append(ptp)
            elif child.tag in {"tuplet"}:
                tuplet = self._visit_tuplet(child, time_mod)
                if tuplet is not None:
                    output.append(tuplet)
            elif child.tag == "arpeggiate":
                output.append(self._visit_arpeggiate(child, pitch))
            elif child.tag == "fermata":
                output.append(self._visit_fermata())
            elif child.tag == "ornaments":
                output += self._visit_ornaments(child, pitch)
            # elif child.tag == "technical":
            #     output += self._visit_technical(child)
            elif child.tag == "articulations":
                output += self._visit_articulations(child, pitch)
            elif child.tag == "dynamics":
                output += self._visit_dynamics(child)
        return output

    @staticmethod
    def _get_number(node: ET.Element) -> Optional[int]:
        number_node = node.get("number", None)
        number = int(number_node) if number_node is not None else None
        return number

    def _visit_tuplet(
        self,
        tuplet: ET.Element,
        time_mod: Optional[Fraction],
    ) -> Optional[MTN.AST.Tuplet]:
        """Visit tuplet node."""
        tuplet_number = None
        number = self._get_number(tuplet)
        tuplet_type = tuplet.get("type")
        if tuplet_type is None:
            raise ValueError("A tied element has no compulsory attribute 'type'.")
        tuplet_value = STARTSTOP_MXML2MTN[MXML.TT.StartStop(tuplet_type)]
        show_number = not tuplet.get("show-number", "none") == "none"
        show_bracket = not tuplet.get("bracket", "no") == "no"

        if show_number:
            if time_mod is None:
                actual_elm = tuplet.find("tuplet-actual")
                if actual_elm is None:
                    raise ValueError("Actual Tuplet value missing")
                tpnmb = actual_elm.find("tuplet-number")
                if tpnmb is None:
                    raise ValueError("Actual Tuplet value missing")

                number_element = tpnmb.text
            else:
                number_element = str(time_mod.numerator)
            if tuplet_value == MTN.TT.StartStop.START:
                tuplet_number = MTN.AST.Number(
                    [self._number_token(int(x), None) for x in number_element]
                )
        ident = self.symbol_table.identify_point_to_point(
            MTN.TT.TokenType.TUPLET, number
        )

        token = MTN.AST.Token(
            MTN.TT.TokenType.TUPLET,
            {"type": tuplet_value},
            MTN.MS.StaffPosition(None, None),
            ident,
        )
        if not show_bracket and not show_number:
            return None

        return MTN.AST.Tuplet(tuplet_number, token)

    def _visit_tied(
        self,
        tied: ET.Element,
        pitch: MTN.MS.StaffPosition,
    ) -> Optional[MTN.AST.Token]:
        """Convert MXML tied element into MTN equivalent."""
        number = self._get_number(tied)
        identifier = self.symbol_table.identify_tie(pitch, number)

        tied_type = tied.get("type")
        if tied_type is None:
            raise ValueError("A tied element has no compulsory attribute 'type'.")
        position = MXML.TT.TiedType(tied_type)

        if position in {MXML.TT.TiedType.CONTINUE, MXML.TT.TiedType.LET_RING}:
            return None

        return MTN.AST.Token(
            MTN.TT.TokenType.TIED,
            {"type": TIED_TYPE_MXML2MTN[position]},
            pitch,
            identifier,
        )

    def _visit_point_to_point(
        self,
        element: ET.Element,
        pitch: MTN.MS.StaffPosition,
    ) -> Optional[MTN.AST.Token]:
        """Convert MXML point to point element into MTN equivalent."""
        name = element.tag
        ptp_type = element.get("type")
        if ptp_type is None:
            raise ValueError("A p2p element has no compulsory attribute 'type'.")

        # Grab any other value that is not really interesting
        try:
            position = MXML.TT.StartStop(ptp_type)
        except ValueError:
            return None

        number = self._get_number(element)
        try:
            token_type = P2P_TOKENS[name]
        except KeyError as exc:
            raise UnsupportedElement(
                f"Unknown or unsupported end-to-end token '{name}'"
            ) from exc

        identifier = self.symbol_table.identify_point_to_point(token_type, number)

        return MTN.AST.Token(
            token_type,
            {"type": STARTSTOP_MXML2MTN[position]},
            pitch,
            identifier,
        )

    def _visit_arpeggiate(
        self,
        arpeggiate: ET.Element,
        pitch: MTN.MS.StaffPosition,
    ) -> MTN.AST.Token:
        """Convert MXML arpeggiate element into MTN equivalent if possible."""
        number = self._get_number(arpeggiate)
        identifier = self.symbol_table.identify_arpeggios(
            self.state.current_time, number
        )
        return MTN.AST.Token(MTN.TT.TokenType.ARPEGGIATE, {}, pitch, identifier)

    def _visit_ornaments(
        self,
        ornaments: ET.Element,
        pitch: MTN.MS.StaffPosition,
    ) -> List[MTN.AST.Token]:
        """Convert MXML ornaments element into list of MTN equivalents."""
        output: List[MTN.AST.Token] = []
        for child in ornaments:
            if child.tag in ORNAMENT_TOKENS:
                output.append(
                    MTN.AST.Token(
                        ORNAMENT_TOKENS[child.tag],
                        {},
                        pitch,
                        self.symbol_table.give_identifier(),
                    )
                )
        return output

    def _visit_articulations(
        self,
        articulations: ET.Element,
        pitch: MTN.MS.StaffPosition,
    ) -> List[MTN.AST.Token]:
        """Convert MXML articulations element into list of MTN equivalents."""
        output: List[MTN.AST.Token] = []
        for child in articulations:
            if child.tag in ARTICULATION_TOKENS:
                output.append(
                    MTN.AST.Token(
                        ARTICULATION_TOKENS[child.tag],
                        {},
                        pitch,
                        self.symbol_table.give_identifier(),
                    )
                )
        return output

    def _visit_stem(self, stem: ET.Element) -> Optional[MTN.AST.Token]:
        """Create MTN stem object from MXML stem element.

        Parameters
        ----------
        stem : ET.Element
            MXML stem element.

        Returns
        -------
        Optional[MTN.AST.Stem]
            Equivalent MTN element. If the stem is not to be shown, returns None.
        """
        assert stem.text is not None, "Empty stem contents"
        stem_type = MXML.TT.StemValue(stem.text)
        if stem_type == MXML.TT.StemValue.NONE:
            return None
        elif stem_type == MXML.TT.StemValue.DOUBLE:
            # TODO: Fix the double stem. For now just assume one of them is present
            ...
        stem_token = MTN.AST.Token(
            MTN.TT.TokenType.STEM,
            {"type": STEM_MXML2MTN[stem_type]},
            MTN.MS.StaffPosition(None, None),
            self.symbol_table.give_identifier(),
        )

        return stem_token

    def _visit_notehead(
        self,
        notehead: ET.Element,
    ) -> Tuple[Optional[MTN.AST.Token], bool]:
        """Create MTN notehead object from MXML notehead element.

        Returns
        -------
        MTN.AST.Token
            Token representing the notehead.
        bool
            Whether or not the element should be visible.
        """
        assert notehead.text is not None, "Empty notehead contents"
        nh_type = MXML.TT.NoteheadValue(notehead.text)

        if nh_type == MXML.TT.NoteheadValue.NORMAL:
            return None, True

        if nh_type in NHEAD_MXML2MTN:
            modifiers: Dict[str, Any] = {"type": NHEAD_MXML2MTN[nh_type]}
            return (
                MTN.AST.Token(
                    MTN.TT.TokenType.NOTEHEAD,
                    modifiers,
                    MTN.MS.StaffPosition(None, None),
                    self.symbol_table.give_identifier(),
                ),
                True,
            )
        if nh_type == MXML.TT.NoteheadValue.NONE:
            return None, False
        raise UnsupportedElement(f"Unsupported notehead type: {str(nh_type)}")

    def _visit_pitch(
        self,
        pitch: ET.Element,
    ) -> MTN.MS.NotePitch:
        """Extract note pitch semantics from pitch element.

        Parameters
        ----------
        pitch : ET.Element
            The pitch MXML element.

        Returns
        -------
        MTN.MS.NotePitch
            Extracted pitch using musical semantics.
        """
        step_elm = pitch.find("step")
        octave_elm = pitch.find("octave")
        alter_elm = pitch.find("alter")

        assert (step_elm is not None and step_elm.text is not None) and (
            octave_elm is not None and octave_elm.text is not None
        ), "Invalid pitch element without step/octave information"

        step = MTN.TT.NamedPitch[step_elm.text]
        octave = int(octave_elm.text)

        alter = (
            Fraction.from_float(float(alter_elm.text))
            if alter_elm is not None and alter_elm.text is not None
            else Fraction(0)
        )
        return MTN.MS.NotePitch(step, octave, alter)

    def _visit_unpitched(
        self,
        unpitched: ET.Element,
    ) -> MTN.MS.NotePitch:
        """Extract note pitch semantics from unpitched element.

        Parameters
        ----------
        unpitched : ET.Element
            The unpitched MXML element.

        Returns
        -------
        MTN.MS.NotePitch
            Extracted pitch using musical semantics.
        """
        step_elm = unpitched.find("display-step")
        octave_elm = unpitched.find("display-octave")

        assert (step_elm is not None and step_elm.text is not None) and (
            octave_elm is not None and octave_elm.text is not None
        ), "Invalid pitch element without step/octave information"
        step = MTN.TT.NamedPitch[step_elm.text]
        octave = int(octave_elm.text)

        return MTN.MS.NotePitch(step, octave, Fraction(0))

    def _visit_duration(
        self,
        duration: ET.Element,
    ) -> Fraction:
        """Extract duration semantics from MXML duration element.

        Parameters
        ----------
        duration : ET.Element
            The duration MXML element.

        Returns
        -------
        Fraction
            Extracted duration in fractions of a beat.
        """
        assert duration.text is not None, "Invalid duration element without content"
        return Fraction(int(duration.text), self.state.divisions)

    def _visit_type(
        self,
        ntype: ET.Element,
    ) -> MTN.TT.NoteType:
        """Visit a (note) type element in the MXML tree."""
        assert ntype.text is not None, "Invalid data within note type element"
        tobj = MXML.TT.NoteTypeValue(ntype.text)

        return NTYPE_MXML2MTN[tobj]

    def _visit_dot(
        self,
    ) -> MTN.AST.Token:
        """Visit a dot element in the MXML tree."""
        return MTN.AST.Token(
            MTN.TT.TokenType.DOT,
            {},
            MTN.MS.StaffPosition(None, None),
            self.symbol_table.give_identifier(),
        )

    def _visit_accidental(
        self,
        accidental: ET.Element,
    ) -> List[MTN.AST.Token]:
        """Visit an accidental element in the MXML tree and convert it to MTN."""
        accidental_type = MXML.TT.AccidentalValue(accidental.text)
        compounds: List[MXML.TT.AccidentalValue]

        if accidental_type in ACCIDENTAL_MXML2MTN.keys():
            compounds = [accidental_type]
        elif accidental_type == MXML.TT.AccidentalValue.NATURAL_SHARP:
            compounds = [MXML.TT.AccidentalValue.NATURAL, MXML.TT.AccidentalValue.SHARP]
        elif accidental_type == MXML.TT.AccidentalValue.NATURAL_FLAT:
            compounds = [MXML.TT.AccidentalValue.NATURAL, MXML.TT.AccidentalValue.FLAT]
        elif accidental_type == MXML.TT.AccidentalValue.SHARP_SHARP:
            compounds = [MXML.TT.AccidentalValue.SHARP, MXML.TT.AccidentalValue.SHARP]
        else:
            raise UnsupportedElement(
                f"'{str(accidental_type)}' is an unsupported type of accidental."
            )

        return [
            MTN.AST.Token(
                MTN.TT.TokenType.ACCIDENTAL,
                {"type": ACCIDENTAL_MXML2MTN[acc]},
                MTN.MS.StaffPosition(None, None),
                self.symbol_table.give_identifier(),
            )
            for acc in compounds
        ]

    def _visit_direction(
        self,
        direction: ET.Element,
    ) -> Optional[MTN.AST.Direction]:
        """Visit and process direction node with diverse direction-type elements.

        Parameters
        ----------
        direction : ET.Element
            MXML direction element.

        Returns
        -------
        MTN.AST.Direction
            List of direction nodes under the present direction one.
        """
        staff = 1
        tokens: List[MTN.AST.Token] = []
        self.state.move_buffer()
        for child in direction:
            if child.tag == "direction-type":
                tokens = self._visit_direction_type(child)

            elif child.tag == "staff":
                maybe_staff = child.text
                if maybe_staff is not None:
                    staff = int(maybe_staff)

        for drc in tokens:
            drc.position = MTN.MS.StaffPosition(None, None)

        if len(tokens) > 0:
            output = MTN.AST.Direction(self.state.current_time, tokens)
            output.sort()
            return output
        else:
            return None

    def _visit_direction_type(
        self,
        dir_type: ET.Element,
    ) -> List[MTN.AST.Token]:
        """Check a direction type node for directions.

        Parameters
        ----------
        dir_type : ET.Element
            A direction-type node in the MXML file.

        Returns
        -------
        List[MTN.AST.Token]
            A list of processed directions.
        """
        output: List[MTN.AST.Token] = []
        for child in dir_type:
            if child.tag == "segno":
                output.append(self._visit_segno())
            elif child.tag == "coda":
                output.append(self._visit_coda())
            elif child.tag == "wedge":
                wedge = self._visit_wedge(child)
                if wedge is not None:
                    output.append(wedge)
            elif child.tag == "dynamics":
                dynamics = self._visit_dynamics(child)
                output += dynamics

        return output

    def _visit_dynamics(
        self,
        dynamics: ET.Element,
    ) -> List[MTN.AST.Token]:
        """Produce a dynamics token from a MXML element.

        Parameters
        ----------
        dynamics : ET.Element
            The MusicXML element.

        Returns
        -------
        List[MTN.AST.Token]
            List of dynamics tokens.
        """
        self.state.move_buffer()

        output = []
        for child in dynamics:
            dyn_type = MXML.TT.DynamicsType(child.tag)
            if dyn_type not in {MXML.TT.DynamicsType.OTHER_DYNAMICS}:
                output.append(
                    MTN.AST.Token(
                        token_type=MTN.TT.TokenType.DYN,
                        modifiers={"type": DYNAMICS_MXML2MTN[dyn_type]},
                        position=MTN.MS.StaffPosition(None, None),
                        token_id=self.symbol_table.give_identifier(),
                    )
                )
        return output

    def _visit_wedge(
        self,
        wedge: ET.Element,
    ) -> Optional[MTN.AST.Token]:
        """Generate a Wedge token.

        Parameters
        ----------
        wedge : ET.Element
            The wedge element within the MXML tree.

        Returns
        -------
        Optional[MTN.AST.Token]
            The token representing the starting or ending of the wedge. If it is a
            continuation wedge, it returns None.
        """
        wedge_type = MXML.TT.WedgeType(wedge.get("type"))

        if wedge_type == MXML.TT.WedgeType.CONTINUE:
            return None

        wedge_type_mtn = WEDGE_MXML2MTN[wedge_type]
        wedge_number_attr = wedge.get("number")
        wedge_number = None
        if wedge_number_attr is not None:
            wedge_number = int(wedge_number_attr)

        ident = self.symbol_table.identify_point_to_point(
            MTN.TT.TokenType.WEDGE, wedge_number
        )

        token = MTN.AST.Token(
            token_type=MTN.TT.TokenType.WEDGE,
            modifiers={"type": wedge_type_mtn},
            position=MTN.MS.StaffPosition(None, None),
            token_id=ident,
        )

        return token

    def _visit_attributes(
        self,
        attributes: ET.Element,
    ) -> MTN.AST.Attributes:
        """Process MXML attributes at a specific point in time.

        Parameters
        ----------
        attributes : ET.Element
            The MXML attribute node.

        Returns
        -------
        MTN.AST.Attributes
            The resulting attributes in MTN format.
        """
        self.state.move_buffer()

        key_elements: List[ET.Element] = []
        timesig_elements: List[ET.Element] = []
        clef_elements: List[ET.Element] = []

        for child in attributes:
            if child.tag == "divisions":
                if child.text is not None:
                    self.state.divisions = int(child.text)
            elif child.tag == "staves":
                nstaves = child.text
                nstaves = cast(str, nstaves)
                self.state.change_staves(int(nstaves))
            elif child.tag == "key":
                key_elements.append(child)
            elif child.tag == "time":
                timesig_elements.append(child)
            elif child.tag == "clef":
                clef_elements.append(child)

        output_attributes = MTN.AST.Attributes.make_empty(
            self.state.nstaves,
            self.state.current_time,
        )

        for clef_elm in clef_elements:
            clef = self._visit_clef(clef_elm)
            clef_staff = clef.position[0]
            assert clef_staff is not None, "Invalid staff value for clef"
            output_attributes.set_clef(clef, clef_staff)

        for timesig_elm in timesig_elements:
            timesig, staff = self._visit_time(timesig_elm)
            if staff == self._ALL_STAVES:
                for new_staff in range(1, self.state.nstaves + 1):
                    new_timesig = deepcopy(timesig)
                    token_visitor = VisitorGetTokens()
                    tokens = token_visitor.visit_ast(new_timesig)
                    for tok in tokens:
                        tok.token_id = self.symbol_table.give_identifier()
                        tok.position = MTN.MS.StaffPosition(None, None)
                    output_attributes.set_timesig(new_timesig, new_staff)
            else:
                output_attributes.timesig[staff] = timesig

        # Merge once to account for the new clef and time, since these are needed for
        # the correct position of key accidentals (could merge a dict and pass it as
        # a parameter to the key processing function but I am lazy).
        self.state.attributes = output_attributes

        for key_elm in key_elements:
            key_processed = self._visit_key(key_elm)
            output_attributes.key |= key_processed

        self.state.attributes = output_attributes

        return output_attributes

    def _visit_key(
        self,
        key: ET.Element,
    ) -> Dict[int, MTN.AST.Key]:
        """Visit a key element in MXML and get its information.

        Parameters
        ----------
        key : ET.Element
            The MXML key node.

        Returns
        -------
        Dict[int, MTN.AST.Key]
            A dictionary mapping each staff with the corresponding key.
        """
        staff_val = key.get("number", None)
        if staff_val is None:
            staff = self._ALL_STAVES
        else:
            staff = int(staff_val)

        if key[0].tag in {"cancel", "fifths"}:
            return self._key_fifths(key, staff)
        return self._key_alters(key, staff)

    def _key_fifths(
        self,
        key: ET.Element,
        staff: int,
    ) -> Dict[int, MTN.AST.Key]:
        """Generate the key element denoted by a number of fifths upward or downward.

        Parameters
        ----------
        key : ET.Element
            Element in the MXML tree for a key.
        staff: int
            What staff this key applies to.

        Returns
        -------
        MTN.AST.Key
            Same key in MTN format.
        """
        if staff == self._ALL_STAVES:
            staves = list(range(1, self.state.nstaves + 1))
        else:
            staves = [staff]

        alterations: List[Optional[MTN.TT.AccidentalType]] = [
            None for _ in range(len(MTN.TT.NamedPitch))
        ]
        accidentals: Dict[int, List[MTN.AST.Token]] = {staff: [] for staff in staves}
        naturals: Dict[int, List[MTN.AST.Token]] = {staff: [] for staff in staves}

        for child in key:
            if child.tag == "cancel":
                if child.text is None:
                    continue

                for curr_staff in staves:
                    naturals[curr_staff] = self._key_accidental_tokens(
                        int(child.text),
                        MTN.TT.AccidentalType.ACC_NATURAL,
                        curr_staff,
                    )

            elif child.tag == "fifths":
                if child.text is None:
                    continue
                fifths = int(child.text)
                for curr_staff in staves:
                    accidentals[curr_staff] = self._key_accidental_tokens(
                        fifths,
                        (
                            MTN.TT.AccidentalType.ACC_SHARP
                            if fifths > 0
                            else MTN.TT.AccidentalType.ACC_FLAT
                        ),
                        curr_staff,
                    )
                alterations = MTN.MS.MusicalKey.fifths_alterations(fifths)

        return {
            curr_staff: MTN.AST.Key(
                accidentals[curr_staff], naturals[curr_staff], alterations, fifths
            )
            for curr_staff in staves
        }

    def _key_accidental_tokens(
        self,
        fifths: int,
        accidental: MTN.TT.AccidentalType,
        staff: int,
    ) -> List[MTN.AST.Token]:
        """Compute the accidentals in a key that is denoted with a number of fifths.

        Parameters
        ----------
        fifths : int
            Number of fifths to alter in whichever direction of the circle the sign
            denotes.
        accidental : MTN.TT.AccidentalType
            What kind of accidental to place (in case this is used for naturals).
        staff: int
            The staff index where the elements are to be placed.

        Returns
        -------
        List[MTN.AST.Token]
            List of tokens present in the key at the given staff.
        """
        output: List[MTN.AST.Token] = []
        clef = self.state.attributes.clef[staff]
        assert clef is not None, (
            "Key cannot be processed because there is no key configuration for the "
            "current staff."
        )
        natural_pos = MTN.MS.MusicalKey.fifths_accidental_positions(fifths, clef)
        for pos in natural_pos:
            output.append(
                MTN.AST.Token(
                    token_type=MTN.TT.TokenType.ACCIDENTAL,
                    modifiers={"type": accidental},
                    position=MTN.MS.StaffPosition(staff, pos),
                    token_id=self.symbol_table.give_identifier(),
                )
            )
        return output

    def _key_alters(
        self,
        key: ET.Element,
        staff: int,
    ) -> Dict[int, MTN.AST.Key]:
        """Process a key using a list of arbitrary alterations.

        Parameters
        ----------
        key : ET.Element
            MXML element with the key information.

        Returns
        -------
        MTN.AST.Key
            Same key in MTN format.
        """
        steps = []
        alter_values = []
        alter_symbols = []

        for child in key:
            if child.tag == "key-step":
                if child.text is None:
                    raise ValueError("Invalid empty key-step element.")
                steps.append(MTN.TT.NamedPitch[child.text])

            elif child.tag == "key-alter":
                if child.text is None:
                    raise ValueError("Invalid empty key-step element.")
                value = Fraction.from_decimal(Decimal(child.text))
                alter_values.append(value)

                alter_symbols.append(
                    MTN.TT.AccidentalType.ACC_SHARP
                    if value > 0
                    else MTN.TT.AccidentalType.ACC_FLAT
                )
            elif child.tag == "key-accidental":
                if child.text is not None:
                    mxml_alter = MXML.TT.AccidentalValue(child.text)
                    alter_symbols[-1] = ACCIDENTAL_MXML2MTN[mxml_alter]

        alters: List[Optional[MTN.TT.AccidentalType]] = [
            None for _ in MTN.TT.NamedPitch
        ]
        for sym, step in zip(alter_symbols, steps):
            alters[step.value] = sym

        if staff == self._ALL_STAVES:
            staves = list(range(1, self.state.nstaves + 1))
        else:
            staves = [staff]

        output = {curr_staff: MTN.AST.Key([], [], alters) for curr_staff in staves}

        for curr_staff, elements in output.items():
            elements.accidentals = self._key_alter_tokens(
                steps, alter_symbols, curr_staff
            )

        return output

    def _key_alter_tokens(
        self,
        steps: List[MTN.TT.NamedPitch],
        alters: List[MTN.TT.AccidentalType],
        staff: int,
    ) -> List[MTN.AST.Token]:
        clef = self.state.attributes.clef[staff]
        assert clef is not None, (
            "Key cannot be processed because there is no key configuration for "
            "the current staff."
        )
        output: List[MTN.AST.Token] = []
        for step, symbol in zip(steps, alters):
            position = clef.pitch2pos(
                MTN.MS.NotePitch(step, clef.octave + 1, Fraction(0))
            )
            position = MTN.MS.MusicalKey.ensure_range(position)
            output.append(
                MTN.AST.Token(
                    MTN.TT.TokenType.ACCIDENTAL,
                    {"type": symbol},
                    MTN.MS.StaffPosition(staff, position),
                    token_id=self.symbol_table.give_identifier(),
                )
            )

        return output

    def _visit_clef(
        self,
        clef: ET.Element,
    ) -> MTN.AST.Clef:
        """Visit a clef element in MXML and get its information.

        Parameters
        ----------
        clef : ET.Element
            The MXML clef node.

        Returns
        -------
        MTN.AST.Clef
            A MTN representation of the same clef node.
        """
        sign_element = clef.find("sign")
        assert (
            sign_element is not None and sign_element.text is not None
        ), "Invalid clef symbol without a sign"

        sign = MXML.TT.ClefSign(sign_element.text)
        clef_type = CLEF_MXML2MTN[sign]

        if sign in {MXML.TT.ClefSign.PERCUSSION, MXML.TT.ClefSign.NONE}:
            sign_note = MTN.TT.NamedPitch.G
        elif sign in {MXML.TT.ClefSign.TAB, MXML.TT.ClefSign.JIANPU}:
            raise ValueError("Clef type is not supported")
        else:
            sign_note = SIGN_MXML2MTN[sign]
        modifiers: Dict[str, Any] = {"type": clef_type}

        line_element = clef.find("line")
        staff_element = clef.get("number", "1")
        staff = int(staff_element)

        print_object_element = clef.get("print-object", "yes")
        print_object = print_object_element == "yes"

        octave = MTN.MS.DEFAULT_CLEF_OCTAVE[sign_note]
        oct_change_element = clef.find("clef-octave-change")
        oct_change = None
        if oct_change_element is not None and oct_change_element.text is not None:
            oct_change = int(oct_change_element.text)
            octave += oct_change
            modifiers["oct"] = oct_change

        if line_element is not None and line_element.text is not None:
            clef_position = 2 * int(line_element.text)
        else:
            clef_position = MTN.MS.DEFAULT_CLEF_POSITIONS[sign_note]

        if print_object:
            clef_token = MTN.AST.Token(
                MTN.TT.TokenType.CLEF,
                modifiers,
                MTN.MS.StaffPosition(staff, clef_position),
                self.symbol_table.give_identifier(),
            )
        else:
            clef_token = None
        return MTN.AST.Clef(
            clef_token,
            sign_note,
            octave,
            MTN.MS.StaffPosition(staff, clef_position),
        )

    def _visit_time(
        self,
        time: ET.Element,
    ) -> Tuple[MTN.AST.TimeSignature, int]:
        """Generate time signature object from MXML "time" object.

        Parameters
        ----------
        time : ET.Element
            MXML time object.

        Returns
        -------
        MTN.AST.TimeSignature
            The processed MTN time object.
        int
            Staff where this element should be placed. Positive integer for a specific
            placement or self._ALL_STAVES if it applies to all staves.
        """
        time_type = MXML.TT.TimeSymbol(time.get("symbol", "normal"))
        staff_val: Optional[str] = time.get("number", None)
        if staff_val is None:
            staff = self._ALL_STAVES
        else:
            staff = int(staff_val)

        beats, beat_type = self._extract_beats_and_type(time)

        time_value, parse_tree = self.parse_time(beats, beat_type)
        output = MTN.AST.TimeSignature(None, None, time_value)

        if time.get("print-object", "yes") == "no":
            return output, staff

        if time_type == MXML.TT.TimeSymbol.NORMAL:
            output.compound_time_signature = parse_tree

            interchangeable = time.find("interchangeable")
            if interchangeable is not None:
                int_beats, int_beat_type = self._extract_beats_and_type(interchangeable)
                _, interch_parse = self.parse_time(int_beats, int_beat_type)
                interch = [
                    MTN.AST.Token(
                        MTN.TT.TokenType.TIME_RELATION,
                        {"type": MTN.TT.TimeRelation.TR_EQUALS},
                        MTN.MS.StaffPosition(None, None),
                        self.symbol_table.give_identifier(),
                    )
                ] + interch_parse
                output.compound_time_signature += interch
        elif time_type == MXML.TT.TimeSymbol.CUT:
            output.time_symbol = MTN.AST.Token(
                MTN.TT.TokenType.TIMESIG,
                {"type": MTN.TT.TimeSymbol.TS_CUT},
                MTN.MS.StaffPosition(None, None),
                self.symbol_table.give_identifier(),
            )
        elif time_type == MXML.TT.TimeSymbol.COMMON:
            output.time_symbol = MTN.AST.Token(
                MTN.TT.TokenType.TIMESIG,
                {"type": MTN.TT.TimeSymbol.TS_COMMON},
                MTN.MS.StaffPosition(None, None),
                self.symbol_table.give_identifier(),
            )
        elif time_type == MXML.TT.TimeSymbol.NOTE:
            raise UnsupportedElement("Notes as time signatures are not supported")
        elif time_type == MXML.TT.TimeSymbol.DOTTED_NOTE:
            raise UnsupportedElement("Notes as time signatures are not supported")
        elif time_type == MXML.TT.TimeSymbol.SINGLE_NUMBER:
            raise UnsupportedElement("Single nums as time signatures are not supported")

        return output, staff

    @staticmethod
    def _extract_beats_and_type(node: ET.Element) -> Tuple[List[str], List[str]]:
        """Extract the beat and beat_type elements from a time node.

        Compound time signatures are defined in MusicXML by a sequence of "beat" and
        "beat_type" nodes. The point is that complex time signatures can be defined
        adding various smaller ones. This function gathers them and converts them to
        aligned lists of strings with their contents for further processing.

        Parameters
        ----------
        node : ET.Element
            The time element in a MusicXML file.

        Returns
        -------
        Tuple[List[str], List[str]]
            Two lists containing the number of beats and beat type aligned.
        """
        beats = [x.text for x in node.findall("beats") if x.text is not None]
        beat_type = [x.text for x in node.findall("beat-type") if x.text is not None]

        assert len(beats) == len(
            beat_type
        ), "Uneven number of beats and beat types in time signature."

        return beats, beat_type

    def parse_time(
        self,
        numerators: List[str],
        denominators: List[str],
    ) -> Tuple[Fraction, List[Union[MTN.AST.TimesigFraction, MTN.AST.Token]]]:
        """Convert pairs of time fractions into abstract representation.

        Parameters
        ----------
        numerators : List[str]
            List of numerators as specified in MXML.
        denominators : List[str]
            List of single number denominators as specified in MXML.

        Returns
        -------
        Tuple[Fraction, List[Union[MTN.AST.TimesigFraction, MTN.AST.Token]]]
            The value for the time signature and the parse tree for the set of time
            signatures.
        """
        total = Fraction(0, 1)
        output: List[Union[MTN.AST.TimesigFraction, MTN.AST.Token]] = []
        for ii, (num, den) in enumerate(zip(numerators, denominators)):
            if ii != 0:
                output.append(self._plus_token(1))
            num_terms = num.replace(" ", "").split("+")
            numerator_tokens: List[Union[MTN.AST.Number, MTN.AST.Token]] = []
            num_value = 0
            for jj, term in enumerate(num_terms):
                num_value += int(term)
                if jj != 0:
                    numerator_tokens.append(self._plus_token(1))
                number_tokens = []
                for digit in term:
                    number_tokens.append(self._number_token(int(digit), 1))
                numerator_tokens.append(MTN.AST.Number(number_tokens))
            numerator = MTN.AST.Numerator(numerator_tokens)
            den_value = int(den)
            number_tokens = []
            for digit in den:
                number_tokens.append(self._number_token(int(digit), 1))
            number = MTN.AST.Number(number_tokens)
            denominator = MTN.AST.Denominator(number)
            output.append(MTN.AST.TimesigFraction(numerator, denominator))

            total += Fraction(num_value * 4, den_value)  # Multiply by 4 to get the
            # number of beats, not the fractions over the full note

        return total, output

    def _number_token(self, num: int, staff: Optional[int]) -> MTN.AST.Token:
        return MTN.AST.Token(
            MTN.TT.TokenType.NUMBER,
            {"type": MTN.TT.Digits(num)},
            position=MTN.MS.StaffPosition(staff, None),
            token_id=self.symbol_table.give_identifier(),
        )

    def _plus_token(self, staff: int) -> MTN.AST.Token:
        return MTN.AST.Token(
            MTN.TT.TokenType.PLUS,
            {},
            MTN.MS.StaffPosition(staff, None),
            self.symbol_table.give_identifier(),
        )

    def _visit_barline(
        self,
        barline: ET.Element,
    ) -> Optional[MTN.AST.Barline]:
        """Generate barline top level element.

        Parameters
        ----------
        barline : ET.Element
            A barline MXML element to transform.

        Returns
        -------
        Optional[MTN.AST.Barline]
            The MTN representation of the barline MXML element. None if invisible.
        """
        self.state.move_buffer()

        barline_type = None
        barlines_mtn: List[MTN.TT.BarlineType] = []
        barline_modifiers: List[MTN.AST.Token] = []

        # Wavy lines in barlines will always be of type "continue", which are ignored in
        # the notation anyway since we only care about starting and ending points.
        # Therefore they are not processed here.

        for child in barline:
            if child.tag == "bar-style":
                barline_type = MXML.TT.BarStyle(child.text)
                if barline_type == MXML.TT.BarStyle.NONE:
                    return None
            elif child.tag == "segno":
                barline_modifiers.append(self._visit_segno())
            elif child.tag == "coda":
                barline_modifiers.append(self._visit_coda())
            elif child.tag == "fermata":
                barline_modifiers.append(self._visit_fermata())
            elif child.tag == "repeat":
                barline_modifiers.append(self._visit_repeat(child))

        if barline_type is None:
            barline_type = MXML.TT.BarStyle.REGULAR

        if barline_type in BAR_STYLE_MXML2MTN:
            barlines_mtn = BAR_STYLE_MXML2MTN[barline_type]
        else:
            raise UnsupportedElement("Unsupported barline")

        # Handling timing information of the barline
        if barline.get("location") == "left":
            barline_time = Fraction(0)
        elif (
            barline.get("location") == "right"
            and self.state.attributes.timesig[1] is not None
        ):
            barline_time = self.state.attributes.timesig[1].time_value
        else:
            barline_time = self.state.current_time

        barline_object = MTN.AST.Barline(
            barline_time,
            [
                MTN.AST.Token(
                    MTN.TT.TokenType.BARLINE,
                    {"type": x},
                    MTN.MS.StaffPosition(None, None),
                    self.symbol_table.give_identifier(),
                )
                for x in barlines_mtn
            ],
            barline_modifiers,
        )

        return barline_object

    def _visit_fermata(self) -> MTN.AST.Token:
        """Generate a Fermata token from a MXML element."""
        return MTN.AST.Token(
            MTN.TT.TokenType.FERMATA,
            {},
            MTN.MS.StaffPosition(None, None),
            self.symbol_table.give_identifier(),
        )

    def _visit_wavy_line(self, wavy_line: ET.Element) -> MTN.AST.Token:
        """Generate a wavy line token from a MXML element."""
        raise NotImplementedError

    def _visit_segno(self) -> MTN.AST.Token:
        """Generate a segno token from a MXML element."""
        return MTN.AST.Token(
            MTN.TT.TokenType.SEGNO,
            {},
            MTN.MS.StaffPosition(None, None),
            self.symbol_table.give_identifier(),
        )

    def _visit_coda(self) -> MTN.AST.Token:
        """Generate a coda token from a MXML element."""
        return MTN.AST.Token(
            MTN.TT.TokenType.CODA,
            {},
            MTN.MS.StaffPosition(None, None),
            self.symbol_table.give_identifier(),
        )

    def _visit_repeat(self, repeat: ET.Element) -> MTN.AST.Token:
        """Generate a repeat token from a MXML element."""
        direction = MXML.TT.BackwardForward(repeat.get("direction", "forward"))
        return MTN.AST.Token(
            MTN.TT.TokenType.REPEAT,
            {"type": BWFW_MXML2MTN[direction]},
            MTN.MS.StaffPosition(None, None),
            self.symbol_table.give_identifier(),
        )
