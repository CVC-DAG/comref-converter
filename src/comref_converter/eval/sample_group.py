"""The Common Optical Music Recognition Framework (COMReF) toolset.

Abstraction on groups of samples.

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
from __future__ import annotations

from typing import Dict, List, NamedTuple, Optional, Union, cast

from ..mtn import ast as AST


class MeasureID(NamedTuple):
    work: str
    part: str
    measure: str


class OptionalMeasureID(NamedTuple):
    work: Optional[str]
    part: Optional[str]
    measure: Optional[str]


class SampleGroup:
    def __init__(self, scores: List[AST.Score]) -> None:
        self.scores = scores
        self.index = self._create_index(self.scores)

    @staticmethod
    def _create_index(scores: List[AST.Score]) -> Dict[MeasureID, AST.Measure]:
        index = {}
        for score in scores:
            score_name = score.score_id

            for measure in score.measures:
                part_id = measure.part_id
                measure_id = measure.measure_id

                full_id = MeasureID(score_name, part_id, measure_id)
                index[full_id] = measure

        return index

    def __getitem__(
        self, index: OptionalMeasureID
    ) -> Union[AST.Measure, List[AST.Measure]]:
        if None not in index:
            typed_index = cast(MeasureID, index)
            return self.index[typed_index]
        return self._get_with_none(index)

    def __len__(self) -> int:
        return len(self.index)

    def get_index(self) -> List[MeasureID]:
        return list(self.index.keys())

    def _get_with_none(self, query: OptionalMeasureID) -> List[AST.Measure]:
        chosen_keys = [x for x in self.index.keys() if self._compare(query, x)]
        return [self.index[k] for k in chosen_keys]

    @staticmethod
    def _compare(query: OptionalMeasureID, key: MeasureID) -> bool:
        work_equal = query.work is None or query.work == key.work
        part_equal = query.part is None or query.part == key.part
        measure_equal = query.measure is None or query.measure == key.measure

        return work_equal and part_equal and measure_equal

    def merge(self, other: SampleGroup) -> SampleGroup:
        """Merge two sets of samples into one.

        Parameters
        ----------
        other : SampleGroup
            An independent sample group to merge with the current one.

        Returns
        -------
        SampleGroup
            A sample group with all unique samples in both.
        """
        scores = list(set(self.scores + other.scores))

        return SampleGroup(scores)
