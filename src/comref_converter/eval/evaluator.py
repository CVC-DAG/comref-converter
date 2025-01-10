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
Evaluation object implementation.
"""


from collections import Counter
from copy import deepcopy
from fractions import Fraction
from typing import Any, Dict, List, Optional, Tuple, Union
from warnings import warn

from apted import APTED

from ..mtn import AST
from ..visitor_count_nodes import VisitorCountNodes
from ..visitor_get_notes import VisitorGetNotes
from ..visitor_get_tokens import VisitorGetTokens
from ..visitor_to_apted import VisitorToAPTED
from .apted_tree import AptedTree


class Evaluator:
    def __init__(self) -> None:
        self.total_samples = 0
        self.valid_samples = 0

        self.edits = 0
        self.total_length = 0
        self.total_target_notes = 0
        self.total_source_notes = 0

        # Class to count per class
        self.confmat: Dict[str, Dict[str, int]] = {}

        # Counts considering the predictions
        self.matched_notes = 0
        self.unmatched_source = 0
        self.unmatched_target = 0

        self.perfect_pitch = 0
        self.perfect_staff = 0
        self.perfect_time = 0

        self.cumulative_pitch_error = 0
        self.cumulative_staff_error = 0
        self.cumulative_time_error = Fraction(0)

    def update(
        self,
        source: AST.Measure,
        target: AST.Measure,
    ) -> Tuple[Dict[str, Dict[str, int]], float, Dict[str, Any]]:
        confmat = self._tier1(source, target)
        matching, ted = self._tier2(source, target)
        measure_stats = self._tier3(matching)

        return confmat, ted, measure_stats

    def _tier1(
        self,
        source: AST.Measure,
        target: AST.Measure,
    ) -> Dict[str, Dict[str, int]]:
        token_visitor = VisitorGetTokens()

        source_tokens = list(map(str, token_visitor.visit_ast(source)))
        target_tokens = list(map(str, token_visitor.visit_ast(target)))

        partial_mat = self._compute_conf_matrix(source_tokens, target_tokens)
        self.confmat = self._merge_conf_matrices(self.confmat, partial_mat)

        return partial_mat

    @staticmethod
    def _compute_conf_matrix(
        src: List[str], tgt: List[str]
    ) -> Dict[str, Dict[str, int]]:
        source_counts = Counter(src)
        target_counts = Counter(tgt)

        confmat = {}

        for tok in set(source_counts.keys()) | set(target_counts.keys()):
            source_value = source_counts.get(tok, 0)
            target_value = target_counts.get(tok, 0)
            confmat[tok] = {
                "tp": min(source_value, target_value),
                "fp": max(0, source_value - target_value),
                "fn": max(0, target_value - source_value),
            }
        return confmat

    @staticmethod
    def _merge_conf_matrices(
        source: Dict[str, Dict[str, int]], new: Dict[str, Dict[str, int]]
    ) -> Dict[str, Dict[str, int]]:
        output = deepcopy(source)
        for tok in set(source.keys()) | set(new.keys()):
            if tok in source and tok in new:
                output[tok]["tp"] += new[tok]["tp"]
                output[tok]["fp"] += new[tok]["fp"]
                output[tok]["fn"] += new[tok]["fn"]
            elif tok in new:
                output[tok] = new[tok]
        return output

    @staticmethod
    def compute_precision_recall(
        confmat: Dict[str, Dict[str, int]]
    ) -> Dict[str, Dict[str, float]]:
        """Compute precision-recall from confusion matrix.

        Parameters
        ----------
        confmat : Dict[str, Dict[str, int]]
            A confusion matrix implemented using a dict of dicts. The root dict's keys
            are the names of the various tokens and the values are a dict with true
            positive (tp), false positive (fp) and false negative (fn) counts as values.
        """
        output = {}
        for tok, counts in confmat.items():
            predicted = counts["tp"] + counts["fp"]
            groundtruth = counts["tp"] + counts["fn"]
            output[tok] = {
                "precision": (counts["tp"] / predicted) if predicted > 0 else 0,
                "recall": (counts["tp"] / groundtruth) if groundtruth > 0 else 0,
            }
        return output

    def _tier2(
        self,
        source: AST.Measure,
        target: AST.Measure,
    ) -> Tuple[
        List[Tuple[Union[AST.Note, AST.Rest], Union[AST.Note, AST.Rest]]], float
    ]:
        apted_visitor = VisitorToAPTED()
        note_visitor = VisitorGetNotes()
        node_visitor = VisitorCountNodes()

        source_tree = AptedTree.from_text(apted_visitor.visit_ast(source))
        target_tree = AptedTree.from_text(apted_visitor.visit_ast(target))

        AptedTree.decorate_tree_with_note_ids(source_tree)
        AptedTree.decorate_tree_with_note_ids(target_tree)

        source_notes = note_visitor.visit_ast(source)
        target_notes = note_visitor.visit_ast(target)

        apted_comp = APTED(target_tree, source_tree)

        # TARGET TO SOURCE
        mapping = apted_comp.compute_edit_mapping()
        edits = apted_comp.compute_edit_distance()

        matching_ids, unmatched_tgt, unmatched_src = self._find_matching_notes(mapping)

        matching_notes = [
            (target_notes[ii], source_notes[jj]) for ii, jj in matching_ids
        ]

        target_counts = node_visitor.visit_ast(target)

        self.edits += edits
        self.total_length += target_counts
        self.total_target_notes += len(target_notes)
        self.total_source_notes += len(source_notes)
        self.unmatched_source += len(unmatched_src)
        self.unmatched_target += len(unmatched_tgt)
        self.matched_notes += len(matching_notes)
        return matching_notes, edits / target_counts

    def _tier3(
        self,
        matching: List[Tuple[Union[AST.Note, AST.Rest], Union[AST.Note, AST.Rest]]],
    ) -> Dict[str, Any]:
        perfect_pitch = 0
        perfect_staff = 0
        perfect_time = 0
        offset_pitch = 0
        offset_staff = 0
        offset_time = Fraction(0)
        for target, source in matching:
            tgt_pitch, src_pitch = target.get_pitch(), source.get_pitch()

            pitch_difference = (
                tgt_pitch.position if tgt_pitch.position is not None else 0
            ) - (src_pitch.position if src_pitch.position is not None else 0)

            if pitch_difference == 0:
                perfect_pitch += 1
            offset_pitch += pitch_difference

            staff_difference = (
                tgt_pitch.staff if tgt_pitch.staff is not None else 0
            ) - (src_pitch.staff if src_pitch.staff is not None else 0)

            if staff_difference == 0:
                perfect_staff += 1
            offset_staff += staff_difference

            tgt_delta, src_delta = target.get_delta(), source.get_delta()
            if tgt_delta is None or src_delta is None:
                warn("Invalid time value found in a notehead")
            else:
                time_difference = tgt_delta - src_delta
                if int(time_difference) == 0:
                    perfect_time += 1
                offset_time += time_difference

        self.perfect_pitch += perfect_pitch
        self.perfect_staff += perfect_staff
        self.perfect_time += perfect_time

        self.cumulative_pitch_error += offset_pitch
        self.cumulative_staff_error += offset_staff
        self.cumulative_time_error += offset_time

        if len(matching) == 0:
            return {
                "perfect_pitch": 0.0,
                "perfect_staff": 0.0,
                "perfect_time": 0.0,
                "offset_pitch": 0.0,
                "offset_staff": 0.0,
                "offset_time": 0.0,
            }

        return {
            "perfect_pitch": perfect_pitch / len(matching),
            "perfect_staff": perfect_staff / len(matching),
            "perfect_time": perfect_time / len(matching),
            "offset_pitch": offset_pitch / len(matching),
            "offset_staff": offset_staff / len(matching),
            "offset_time": float(offset_time) / len(matching),
        }

    @staticmethod
    def _increment_count_dict(
        dictionary: Dict[str, int], toks: List[str]
    ) -> Dict[str, int]:
        for tok in toks:
            if tok in dictionary:
                dictionary[tok] += 1
            else:
                dictionary[tok] = 1
        return dictionary

    def summarise(
        self,
    ) -> Tuple[Dict[str, Dict[str, int]], Dict[str, Dict[str, float]], Dict[str, Any]]:
        ter = self.edits / self.total_length

        missing_note_ratio = (
            (self.unmatched_target / self.total_target_notes)
            if self.total_target_notes > 0
            else 0.0
        )
        false_positive_rate = (
            (self.unmatched_source / self.total_source_notes)
            if self.total_source_notes > 0
            else 0.0
        )

        pitch_precision = (
            (self.perfect_pitch / self.matched_notes) if self.matched_notes > 0 else 0.0
        )
        staff_precision = (
            (self.perfect_staff / self.matched_notes) if self.matched_notes > 0 else 0.0
        )
        delta_precision = (
            (self.perfect_time / self.matched_notes) if self.matched_notes > 0 else 0.0
        )

        pitch_shift = (
            (self.cumulative_pitch_error / self.matched_notes)
            if self.matched_notes > 0
            else 0.0
        )
        staff_shift = (
            (self.cumulative_staff_error / self.matched_notes)
            if self.matched_notes > 0
            else 0.0
        )
        delta_shift = (
            (self.cumulative_time_error / self.matched_notes)
            if self.matched_notes > 0
            else Fraction(0)
        )

        return (
            self.confmat,
            self.compute_precision_recall(self.confmat),
            {
                "ter": ter,
                "mnr": missing_note_ratio,
                "fpr": false_positive_rate,
                "pp": pitch_precision,
                "sp": staff_precision,
                "dp": delta_precision,
                "pitch_shift": pitch_shift,
                "staff_shift": staff_shift,
                "delta_shift": float(delta_shift),
            },
        )

    @staticmethod
    def _find_matching_notes(
        matching: List[Tuple[Optional[AptedTree], Optional[AptedTree]]]
    ) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        """Find those notes/rests that should be matched together.

        Parameters
        ----------
        matching : List[Tuple[Optional[AptedTree], Optional[AptedTree]]]
            A list of matching ids, a list of unmatched ids in the target (false
            negatives) and a list of unmatched ids in the source (false positives).
        """
        notes_and_rests = [
            match
            for match in matching
            if (match[0] is not None and match[0].name in {"rest", "note"})
            or (match[1] is not None and match[1].name in {"rest", "note"})
        ]

        matched = [
            (match[0].note_id, match[1].note_id)
            for match in notes_and_rests
            if match[0] is not None
            and match[0].note_id is not None
            and match[1] is not None
            and match[1].note_id is not None
        ]

        unmatched_target = [
            match[0].note_id
            for match in notes_and_rests
            if match[0] is not None
            and match[0].note_id is not None
            and match[1] is None
        ]

        unmatched_source = [
            match[1].note_id
            for match in notes_and_rests
            if match[1] is not None
            and match[1].note_id is not None
            and match[0] is None
        ]

        return matched, unmatched_target, unmatched_source
