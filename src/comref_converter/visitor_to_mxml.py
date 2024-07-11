"""The Common Optical Music Recognition Framework (COMReF) toolset.

Convert MTN AST into MXML.

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


# TODO: This has to be implemented.

import re
import xml.etree.ElementTree as ET
from datetime import datetime
from fractions import Fraction
from typing import Dict, List, Set, Tuple

from .mtn import AST, MS, TT
from .music_state import ScoreState

RE_MEASURE_ID = re.compile(r"[^0-9\.]+")


def _measure_sorting(measure_id: str) -> float:
    try:
        return float(measure_id)
    except ValueError:
        return float(RE_MEASURE_ID.sub("", measure_id)) + 0.5


class VisitorToMXML(AST.Visitor):
    """Implements conversion to MXML."""

    DEFAULT_DOCTYPE = """<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.0 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">"""

    def __init__(self) -> None:
        super().__init__()

        self.state = ScoreState()

        # List of references to duration objects to be modified accordingly
        self.durations: List[Tuple[Fraction, ET.Element]] = []
        self.notes: List[Tuple[MS.StaffPosition, ET.Element]] = []

        # Beams or flags at the current time step
        self.current_level: int = 0
        self.current_tuplets: List[Tuple[int, int]] = []  # ident, tuplet num

    def reset(self) -> None:
        """Restore object state to default."""
        self.state = ScoreState()

        self.durations = []
        self.notes = []
        self.current_level = 0
        self.current_tuplets = []

    def new_measure(self) -> None:
        """Restore object state to start a new measure of the same part."""
        self.state.new_measure()

        self.durations = []
        self.notes = []
        self.current_level = 0
        self.current_tuplets = []

    def visit_ast(self, root: AST.SyntaxNode) -> ET.ElementTree:
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
        base_node = root.accept(self)

        return ET.ElementTree(base_node)

    def visit_score(self, score: AST.Score) -> ET.Element:
        """Perform visiting operation on Score node."""
        root_element = ET.Element("score-partwise")
        # pi = ET.ProcessingInstruction("xml", 'type="1.0" encoding="UTF-8"')
        # root_element.insert(0, pi)

        work_node = ET.SubElement(root_element, "work")
        work_title_node = ET.SubElement(work_node, "work-title")
        work_title_node.text = score.score_id

        ident_node = ET.SubElement(root_element, "identification")
        enc_node = ET.SubElement(ident_node, "encoding")
        sw_node = ET.SubElement(enc_node, "software")
        sw_node.text = "COMReF"
        enc_date = ET.SubElement(enc_node, "encoding-date")
        enc_date.text = datetime.today().strftime("%Y-%m-%d")

        part_list_node = ET.SubElement(root_element, "part-list")

        part_ids = {measure.part_id for measure in score.measures}
        part_measures: Dict[str, List[AST.Measure]] = {
            part_id: [] for part_id in sorted(part_ids)
        }

        for measure in score.measures:
            part_measures[measure.part_id].append(measure)

        for part_id, measures in part_measures.items():
            _ = ET.SubElement(part_list_node, "score-part", attrib={"id": part_id})
            part_node = ET.SubElement(root_element, "part", attrib={"id": part_id})
            measures.sort(key=lambda x: _measure_sorting(x.measure_id))

            for measure in measures:
                part_node.append(measure.accept(self))

        return root_element

    def _create_duration(self, dur: Fraction) -> ET.Element:
        """Create empty duration object and register it to the state.

        Parameters
        ----------
        dur : Fraction
            Duration of the object in fractions of a beat.

        Returns
        -------
        ET.Element
            Empty ElementTree object to be modified later.
        """
        dur_node = ET.Element("duration")
        self.durations.append((dur, dur_node))
        return dur_node

    def _compute_note_duration(self, chord: AST.Chord) -> Fraction:
        raise NotImplementedError()

    def visit_note(self, note: AST.Note) -> ET.Element:
        """Perform visiting operation on Note node."""
        raise NotImplementedError()

    def visit_toplevel(self, toplevel: AST.TopLevel) -> ET.Element:
        """Perform visiting operation on TopLevel node."""
        raise NotImplementedError()

    def visit_token(self, token: AST.Token) -> ET.Element:
        """Perform visiting operation on Token node."""
        raise NotImplementedError()

    def visit_chord(self, chord: AST.Chord) -> ET.Element:
        """Perform visiting operation on Chord node."""
        raise NotImplementedError()

    def visit_rest(self, rest: AST.Rest) -> ET.Element:
        """Perform visiting operation on Rest node."""
        raise NotImplementedError()

    def visit_note_group(self, note_group: AST.NoteGroup) -> ET.Element:
        """Perform visiting operation on NoteGroup node."""
        raise NotImplementedError()

    def visit_attributes(self, attributes: AST.Attributes) -> ET.Element:
        """Perform visiting operation on Attributes node."""
        raise NotImplementedError()

    def visit_time_signature(self, time_signature: AST.TimeSignature) -> ET.Element:
        """Perform visiting operation on TimeSignature node."""
        raise NotImplementedError()

    def visit_key(self, key: AST.Key) -> ET.Element:
        """Perform visiting operation on Key node."""
        raise NotImplementedError()

    def visit_clef(self, clef: AST.Clef) -> ET.Element:
        """Perform visiting operation on Clef node."""
        raise NotImplementedError()

    def visit_direction(self, direction: AST.Direction) -> ET.Element:
        """Perform visiting operation on Direction node."""
        raise NotImplementedError()

    def visit_measure(self, measure: AST.Measure) -> ET.Element:
        """Perform visiting operation on Measure node."""
        measure_node = ET.Element("measure", attrib={"number": measure.measure_id})

        self.state.change_staves(measure.staves)

        # FIXME: If there is a staff number change but there are no elements, add attributes anyway
        for ii, child in enumerate(measure.elements):
            child_node = child.accept(self)
            if measure.staves != self.state.nstaves:
                self.state.change_staves(measure.staves)
                if ii == 0 and isinstance(child, AST.Attributes):
                    ...  # TODO: Add to existing attributes node
                else:
                    ...  # TODO: Create new attributes node
            measure_node.append(child_node)

        return measure_node

    def visit_barline(self, barline: AST.Barline) -> ET.Element:
        """Perform visiting operation on Barline node."""
        raise NotImplementedError()

    def visit_tuplet(self, tuplet: AST.Tuplet) -> ET.Element:
        """Perform visiting operation on Tuplet node."""
        raise NotImplementedError()

    def visit_numerator(self, numerator: AST.Numerator) -> ET.Element:
        """Perform visiting operation on Numerator node."""
        raise NotImplementedError()

    def visit_denominator(self, denominator: AST.Denominator) -> ET.Element:
        """Perform visiting operation on Denominator node."""
        raise NotImplementedError()

    def visit_number(self, number: AST.Number) -> ET.Element:
        """Perform visiting operation on Number node."""
        raise NotImplementedError()

    def visit_timesig_fraction(self, fraction: AST.TimesigFraction) -> ET.Element:
        """Perform visiting operation on timesig fraction node."""
        raise NotImplementedError()
