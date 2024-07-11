"""The Common Optical Music Recognition Framework (COMREF) toolset.

Test on a set of engineered edge cases and complex settings.

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
import json
import logging
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Tuple
from zipfile import ZipFile

from tabulate import tabulate

from .. import comref_converter as comref

logging.basicConfig(filename="test_complex.log", level=logging.DEBUG)
LOGGER = logging.getLogger()


class TestScenarios(unittest.TestCase):
    """Small tests for specific edge cases and difficult scenarios."""

    COMPLEX_FNAME = Path(__file__).parent / "complex.mxl"
    COMPLEX_GTRUTH = Path(__file__).parent / "complex_reference.mtn"

    MOVING_VOICES_FNAME = Path(__file__).parent / "moving_voices.mxl"
    MOVING_VOICES_GTRUTH = Path(__file__).parent / "moving_voices_reference.mtn"

    TIMESIG_CHANGES_FNAME = Path(__file__).parent / "timesig_changes.mxl"
    TIMESIG_CHANGES_GTRUTH = Path(__file__).parent / "timesig_changes_reference.mtn"

    BREAKING_BEAMS_FNAME = Path(__file__).parent / "breaking_beams.mxl"
    BREAKING_BEAMS_GTRUTH = Path(__file__).parent / "breaking_beams_reference.mtn"

    CLEF_CHANGES_FNAME = Path(__file__).parent / "clef_changes.mxl"
    CLEF_CHANGES_GTRUTH = Path(__file__).parent / "clef_changes_reference.mtn"

    MIDMEASURE_CHANGE_FNAME = Path(__file__).parent / "midmeasure_change.mxl"
    MIDMEASURE_CHANGE_GTRUTH = Path(__file__).parent / "midmeasure_change_reference.mtn"

    def _run_end_to_end_test(self, source: Path, target: Path) -> None:
        with ZipFile(source) as f_zip:
            file_list = f_zip.namelist()
            with f_zip.open(file_list[-1], "r") as xml_file:
                mxml = ET.parse(xml_file)
        translator = comref.TranslatorMXML()
        mtn = translator.translate(mxml.getroot(), source.stem, set())

        xml_visitor = comref.VisitorToXML()
        xml_ast = xml_visitor.visit_ast(mtn)
        xml_tree = ET.ElementTree(xml_ast)
        ET.indent(xml_tree, space="    ")
        xml_tree.write(source.parent / f"{source.stem}_generated.mtn")

        with open(target) as f_gt:
            gt_root = ET.parse(f_gt).getroot()
            translator = comref.TranslatorXML()
            gt = translator.translate(gt_root, target.stem, set())

        for mtn_measure, gt_measure in zip(mtn.measures, gt.measures):
            self.assertEqual(mtn_measure.measure_id, gt_measure.measure_id)
            self.assertEqual(mtn_measure.part_id, gt_measure.part_id)

            LOGGER.info(
                f"Analising Measure {gt_measure.measure_id} - Part {gt_measure.part_id}"
            )
            LOGGER.debug(
                "Produced measure: \n"
                + "====" * 10
                + "\n"
                + str(mtn_measure)
                + "\n"
                + "====" * 10
                + "\n"
                + "Reference measure: \n"
                + "====" * 10
                + "\n"
                + str(gt_measure)
                + "\n"
            )
            # Left / right barlines are not in the child pool of the measure.

            if (
                gt_measure.left_barline is not None
                and mtn_measure.left_barline is not None
            ):
                gt_measure.left_barline.compare_raise(mtn_measure.left_barline)
            elif not (
                gt_measure.left_barline is None and mtn_measure.left_barline is None
            ):
                raise ValueError("Mismatch on left barlines in measure")

            if (
                gt_measure.right_barline is not None
                and mtn_measure.right_barline is not None
            ):
                gt_measure.right_barline.compare_raise(mtn_measure.right_barline)
            elif not (
                gt_measure.right_barline is None and mtn_measure.right_barline is None
            ):
                raise ValueError("Mismatch on right barlines in measure")

            for ii, (mtn_node, gt_node) in enumerate(
                zip(mtn_measure.elements, gt_measure.elements)
            ):
                with self.subTest(
                    i=ii,
                    msg=f"Subtest {ii}: {gt_measure.part_id} - {gt_measure.measure_id}",
                ):
                    try:
                        gt_node.compare_raise(mtn_node)
                    except Exception:
                        LOGGER.info(
                            f"Failed on toplevel node {ii}: \n"
                            + str(mtn_node)
                            + "\n"
                            + "It should be: \n"
                            + str(gt_node)
                        )
                        raise

    def test_complex_xml_no_feedback(self) -> None:
        self._run_end_to_end_test(self.COMPLEX_FNAME, self.COMPLEX_GTRUTH)

    def test_moving_voices_xml_no_feedback(self) -> None:
        self._run_end_to_end_test(self.MOVING_VOICES_FNAME, self.MOVING_VOICES_GTRUTH)

    def test_breaking_beams_xml_no_feedback(self) -> None:
        self._run_end_to_end_test(self.BREAKING_BEAMS_FNAME, self.BREAKING_BEAMS_GTRUTH)

    def test_timesig_changes_xml_no_feedback(self) -> None:
        self._run_end_to_end_test(
            self.TIMESIG_CHANGES_FNAME, self.TIMESIG_CHANGES_GTRUTH
        )

    def test_clef_changes_xml_no_feedback(self) -> None:
        self._run_end_to_end_test(self.CLEF_CHANGES_FNAME, self.CLEF_CHANGES_GTRUTH)

    def test_midmeasure_change_xml_no_feedback(self) -> None:
        self._run_end_to_end_test(
            self.MIDMEASURE_CHANGE_FNAME, self.MIDMEASURE_CHANGE_GTRUTH
        )
