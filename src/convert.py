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
Format conversion script.
"""
import json
import xml.etree.ElementTree as ET
from argparse import ArgumentParser, Namespace
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Set
from zipfile import ZipFile

import comref_converter as comref

# class MtnEncoder(json.JSONEncoder):
#     """Custom encoder to handle MTN special types."""

#     def default(self, o) -> Any:
#         """Convert into json."""
#         if isinstance(o, comref.TokenType):
#             return str(o.name)
#         if isinstance(o, Fraction):
#             return f"{o.numerator}/{o.denominator}"
#         if isinstance(o, comref.MS.AccidentalType):
#             return str(o.value)
#         if isinstance(o, comref.MS.NamedPitch):
#             return o.value
#         if isinstance(o, comref.MS.StaffPosition):
#             return {"s": o.staff, "p": o.position}
#         return json.JSONEncoder.default(self, o)


def preprocess_mxml(mxml_file: Path) -> ET.Element:
    """Load compressed MXL file as XML."""
    with ZipFile(mxml_file) as f_zip:
        file_list = [x for x in f_zip.namelist() if "META-INF/" not in x]
        with f_zip.open(file_list[0], "r") as xml_file:
            root = ET.parse(xml_file)
    return root.getroot()


def preprocess_unzipped_mxml(mxml_file: Path) -> ET.Element:
    """Load unzipped xml file."""
    root = ET.parse(mxml_file)
    return root.getroot()


def preprocess_unzipped_mtn(mtn_file: Path) -> ET.Element:
    """Load unzipped xml file."""
    root = ET.parse(mtn_file)
    return root.getroot()


def export_mtn(
    data: ET.Element,
    output_path: Path,
) -> None:
    root = ET.ElementTree(data)
    ET.indent(root, space="    ", level=0)
    with open(output_path, "w", encoding="utf8") as f_out:
        root.write(f_out, encoding="unicode")


def export_unzipped_mxml(
    data: ET.ElementTree,
    output_path: Path,
) -> None:
    ET.indent(data, space="    ", level=0)
    with open(output_path, "w", encoding="utf8") as f_out:
        data.write(f_out, encoding="unicode")


def export_seq(
    data: Dict[comref.MeasureID, List[str]],
    output_path: Path,
) -> None:
    with open(output_path, "w") as f_out:
        json.dump(
            {f"p{part}_m{measure}": ",".join(v) for (part, measure), v in data.items()},
            f_out,
            indent=4,
        )


def export_plaintext(
    data: str,
    output_path: Path,
) -> None:
    with open(output_path, "w", encoding="utf8") as f_out:
        f_out.write(data)


def export_json(
    data: Dict[Any, Any],
    output_path: Path,
) -> None:
    with open(output_path, "w", encoding="utf8") as f_out:
        json.dump({f"p{k[0]}_m{k[1]}": v for k, v in data.items()}, f_out, indent=4)


def load_feedback(feedback: Path) -> Set[comref.MeasureID]:
    """Load feedback file into the MeasureID format."""
    with open(feedback, "r", encoding="utf8") as f_in:
        line_list = json.load(f_in)
    output = {(str(x[0]), str(x[1])) for x in line_list}
    return output


def __identity(*_: Any) -> None:
    print("This operation is not implemented.")
    return None


class ConversionFormat(Enum):
    """Supported conversion formats."""

    CF_MXML = "mxml"
    CF_UNZIPPED_MXML = "unzipped-mxml"
    CF_MEI = "mei"
    CF_MTN = "mtn"
    CF_SEQ = "seq"
    CF_APT = "apt"
    CF_DOT = "dot"
    CF_ABARO = "abaro"


EXTENSIONS = {
    ".mxl": ConversionFormat.CF_MXML,
    ".musicxml": ConversionFormat.CF_UNZIPPED_MXML,
    ".mei": ConversionFormat.CF_MEI,
    ".mtn": ConversionFormat.CF_MTN,
    ".seq": ConversionFormat.CF_SEQ,
    ".apt": ConversionFormat.CF_APT,
    ".dot": ConversionFormat.CF_DOT,
    ".abaro": ConversionFormat.CF_ABARO,
}


PREPROCESSORS: Dict[ConversionFormat, Callable] = {
    ConversionFormat.CF_MXML: preprocess_mxml,
    ConversionFormat.CF_UNZIPPED_MXML: preprocess_unzipped_mxml,
    ConversionFormat.CF_MEI: __identity,
    ConversionFormat.CF_MTN: preprocess_unzipped_mtn,
    ConversionFormat.CF_SEQ: __identity,
    ConversionFormat.CF_ABARO: __identity,
}

EXPORTERS = {
    ConversionFormat.CF_MXML: __identity,
    ConversionFormat.CF_UNZIPPED_MXML: export_unzipped_mxml,
    ConversionFormat.CF_MEI: __identity,
    ConversionFormat.CF_MTN: export_mtn,
    ConversionFormat.CF_SEQ: export_seq,
    ConversionFormat.CF_APT: export_plaintext,
    ConversionFormat.CF_DOT: export_plaintext,
    ConversionFormat.CF_ABARO: export_json,
}


FORMAT_TRANSLATORS = {
    ConversionFormat.CF_MXML: comref.TranslatorMXML,
    ConversionFormat.CF_UNZIPPED_MXML: comref.TranslatorMXML,
    ConversionFormat.CF_MEI: comref.TranslatorMEI,
    ConversionFormat.CF_MTN: comref.TranslatorXML,
    ConversionFormat.CF_SEQ: comref.TranslatorSequence,
}

FORMAT_VISITORS = {
    ConversionFormat.CF_MXML: comref.VisitorToMXML,
    ConversionFormat.CF_UNZIPPED_MXML: comref.VisitorToMXML,
    ConversionFormat.CF_MEI: comref.VisitorToMEI,
    ConversionFormat.CF_MTN: comref.VisitorToXML,
    ConversionFormat.CF_SEQ: comref.VisitorToModelSequence,
    ConversionFormat.CF_APT: comref.VisitorToAPTED,
    ConversionFormat.CF_DOT: comref.VisitorToDOT,
    ConversionFormat.CF_ABARO: comref.VisitorToABaro,
}


def main(args: Namespace) -> None:
    if args.feedback is not None:
        feedback = load_feedback(args.feedback)
    else:
        feedback = set()

    if args.infmt is None:
        infmt = EXTENSIONS[args.source.suffix]
    else:
        infmt = args.infmt

    if args.outfmt is None:
        outfmt = EXTENSIONS[args.target.suffix]
    else:
        outfmt = args.outfmt

    print(infmt, outfmt)

    preprocessed = PREPROCESSORS[infmt](args.source)
    translator = FORMAT_TRANSLATORS[infmt]()
    mtn_element = translator.translate(preprocessed, args.source.stem, feedback)
    visitor = FORMAT_VISITORS[outfmt]()
    output_element = visitor.visit_ast(mtn_element)

    EXPORTERS[outfmt](output_element, args.target)


def setup() -> Namespace:
    parser = ArgumentParser()

    parser.add_argument(
        "source",
        help="File to extract information from.",
        type=Path,
    )

    parser.add_argument(
        "target",
        help="Output file to store the converted piece into.",
        type=Path,
    )

    parser.add_argument(
        "--infmt",
        help="Format from which to convert the file (if you want to force a specific "
        "encoding and/or if your file's format cannot be inferred from the "
        "extension).",
        choices=[x.value for x in ConversionFormat],
        type=ConversionFormat,
        default=None,
    )

    parser.add_argument(
        "--outfmt",
        help="Format into which to convert the file (if you want to force a specific "
        "encoding and/or if your file's format cannot be inferred from the "
        "extension).",
        choices=[x.value for x in ConversionFormat],
        type=ConversionFormat,
        default=None,
    )
    parser.add_argument(
        "--feedback",
        help="Whether or not an engraving feedback file should be used.",
        type=Path,
        default=None,
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    main(setup())
