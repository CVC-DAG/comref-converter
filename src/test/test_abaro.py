# The Common Optical Music Recognition Framework (COMREF) toolset.
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
Test generation of ABaro strings.
"""

import json
import logging
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

from .. import comref_converter as comref

logging.basicConfig(filename="test_abaro_monophonic.log", level=logging.DEBUG)
LOGGER = logging.getLogger()


class TestAbaro(unittest.TestCase):
    MONOPHONIC = Path(__file__).parent / "abaro_monophonic.mxl"
    MONOPHONIC_GTRUTH = Path(__file__).parent / "abaro_monophonic_reference.json"

    def _run_abaro_test(self, source: Path, target: Path) -> None:
        with ZipFile(source) as f_zip:
            file_list = f_zip.namelist()
            with f_zip.open(file_list[-1], "r") as xml_file:
                mxml = ET.parse(xml_file)

        with open(target, "r") as f_target:
            abaro_target = json.load(f_target)

        translator = comref.TranslatorMXML()
        mtn = translator.translate(mxml.getroot(), source.stem, set())
        xml_visitor = comref.VisitorToXML()
        xml_ast = xml_visitor.visit_ast(mtn)
        xml_tree = ET.ElementTree(xml_ast)
        ET.indent(xml_tree, space="    ")
        xml_tree.write(source.parent / f"{source.stem}_generated.mtn")

        abaro_visitor = comref.VisitorToABaro()
        abaro_output = abaro_visitor.visit_ast(mtn)
        abaro_output = {f"p{k[0]}_m{k[1]}": v for k, v in abaro_output.items()}

        with open(source.parent / f"{source.stem}_generated.abaro", "w") as f_out:
            json.dump(abaro_output, f_out, indent=4)

        for ii, measure_id in enumerate(
            set(list(abaro_output.keys()) + list(abaro_target.keys()))
        ):
            with self.subTest(
                i=ii,
                msg=f"Subtest {ii}: {measure_id}",
            ):
                LOGGER.info(f"Analising Measure {measure_id}")
                LOGGER.debug(
                    "Produced measure: \n"
                    + "====" * 10
                    + "\n"
                    + "~".join(abaro_output[measure_id])
                    + "\n"
                    + "====" * 10
                    + "\n"
                    + "Reference measure: \n"
                    + "====" * 10
                    + "\n"
                    + "~".join(abaro_target[measure_id])
                    + "\n"
                )
                self.assertEqual(abaro_output[measure_id], abaro_target[measure_id])

    def test_abaro_monophonic(self) -> None:
        self._run_abaro_test(self.MONOPHONIC, self.MONOPHONIC_GTRUTH)
