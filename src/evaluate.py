"""The Common Optical Music Recognition Framework (COMReF) toolset.

Evaluation script.

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
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Any, Dict, Tuple
from xml.etree import ElementTree as ET

from comref_converter import AST, TranslatorXML
from comref_converter import eval as EVAL
from tqdm.auto import tqdm


def nest_on_measure_id(
    input_dict: Dict[Tuple[str, str, str], Any]
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    output_dict: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for (name, part, measure), data in input_dict.items():
        if name in output_dict:
            if part in output_dict[name]:
                output_dict[name][part][measure] = data
            else:
                output_dict[name][part] = {measure: data}
        else:
            output_dict[name] = {part: {measure: data}}

    return output_dict


def main(args: Namespace) -> None:
    if not args.out.exists():
        args.out.mkdir(parents=True)

    if args.predictions is not None:
        paths = args.predictions
    else:
        with open(args.prediction_list, "r", encoding="utf8") as f_list:
            prediction_list = json.load(f_list)
        paths = [args.prediction_list.parent / x for x in prediction_list]

    predictions = []
    loaded = 0
    for path in paths:
        try:
            predictions.append(load_mtn_file(path))
            loaded += 1
        except Exception:
            print(f"CAREFUL: Could not load {path}")

    print(f"Loaded {loaded} out of {len(paths)} prediction files.")

    if args.targets is not None:
        paths = args.targets
    else:
        with open(args.target_list, "r") as f_list:
            target_list = json.load(f_list)
        paths = [args.target_list.parent / x for x in target_list]

    targets = []
    loaded = 0
    for path in paths:
        try:
            targets.append(load_mtn_file(path))
            loaded += 1
        except Exception as e:
            print(f"CAREFUL: Could not load {path}: {str(e)}")

    print(f"Loaded {loaded} out of {len(paths)} ground truth files.")

    prediction_loader = EVAL.SampleGroup(predictions)
    target_loader = EVAL.SampleGroup(targets)

    shared = list(set(prediction_loader.get_index()) & set(target_loader.get_index()))
    print(
        f"There are {len(shared)} shared measures from {len(prediction_loader)} "
        f"predicted measures and {len(target_loader)} target measures."
    )
    evaluator = EVAL.Evaluator()

    confmat_dict = {}
    ter_dict = {}
    measure_stats_dict = {}

    for measure in tqdm(shared):
        (
            confmat_dict[measure],
            ter_dict[measure],
            measure_stats_dict[measure],
        ) = evaluator.update(prediction_loader[measure], target_loader[measure])

    confmat, precrec, summary = evaluator.summarise()

    with open(
        args.out / "measure_confusion_matrix.json",
        "w",
        encoding="utf8",
    ) as f_out:
        json.dump(nest_on_measure_id(confmat_dict), f_out, indent=4)

    with open(
        args.out / "ter.json",
        "w",
        encoding="utf8",
    ) as f_out:
        json.dump(nest_on_measure_id(ter_dict), f_out, indent=4)

    with open(
        args.out / "measure_summary.json",
        "w",
        encoding="utf8",
    ) as f_out:
        json.dump(nest_on_measure_id(measure_stats_dict), f_out, indent=4)

    with open(
        args.out / "confusion_matrix.json",
        "w",
        encoding="utf8",
    ) as f_out:
        json.dump(confmat, f_out, indent=4)

    with open(
        args.out / "precision_recall.json",
        "w",
        encoding="utf8",
    ) as f_out:
        json.dump(precrec, f_out, indent=4)

    with open(
        args.out / "summary.json",
        "w",
        encoding="utf8",
    ) as f_out:
        json.dump(summary, f_out, indent=4)


def load_mtn_file(path: Path) -> AST.Score:
    translator = TranslatorXML()
    tree = ET.parse(path)

    return translator.translate(tree.getroot(), "", set())


def setup() -> Namespace:
    parser = ArgumentParser()

    preds_group = parser.add_mutually_exclusive_group(required=True)

    preds_group.add_argument(
        "--predictions",
        type=Path,
        nargs="+",
        help="MTN files containing predictions.",
        metavar="<PATH TO FILE>",
    )
    preds_group.add_argument(
        "--prediction_list",
        type=Path,
        help="Single JSON file containing a list of relative paths to predictions.",
        metavar="<PATH TO FILE>",
    )

    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument(
        "--targets",
        type=Path,
        nargs="+",
        help="MTN files containing ground truth.",
        metavar="<PATH TO FILE>",
    )
    target_group.add_argument(
        "--target_list",
        type=Path,
        help="Single JSON file containing a list of relative paths to ground truth.",
        metavar="<PATH TO FILE>",
    )

    parser.add_argument(
        "--out",
        type=Path,
        help="Folder where output files will be stored. Default: <Working Dir> / Eval",
        default=Path(__file__).parent,
    )

    args = parser.parse_args()

    return args


if __name__ == "__main__":
    main(setup())
