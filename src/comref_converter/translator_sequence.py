"""The Common Optical Music Recognition Framework (COMReF) toolset.

Implementation of a sequence-to-mtn loader.

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

import re
from typing import List, Set, Tuple

from .mtn import ast as AST
from .translator_base import MeasureID, Translator


class ParseError(Exception):
    def __init__(self, msg: str, tok_index: int) -> None:
        super().__init__((msg,))
        self.tok_index = tok_index


class TranslatorSequence(Translator):
    """Translator from Seq2Seq to MTN."""

    RE_POSITION = re.compile(r"s:(ANY|[0-9]+)/p:(ANY|\-?[0-9]+)")
    RE_DELTA = re.compile(r"DELTA:(\-?[0-9]+/[0-9]+)")

    def __init__(self) -> None:
        self.tokens: List[AST.Token] = []

        self.index = 0

    def translate(
        self,
        score_in: List[str],
        score_id: str,
        engr_first_line: Set[MeasureID],
    ) -> AST.Score:
        """Translate a score MTN.

        Parameters
        ----------
        score_in : Any
            The representation of the input score in any supported type.
        engr_first_line : Set[MeasureID]
            Set of measure identifiers for those systems that lie at the beginning of a
            line (and thus need a refresh of clef and key elements).

        Returns
        -------
        Dict[MeasureID, AST.Measure]
            A dictionary with measure identifiers as keys and the measure converted to
            MTN as values.
        """
        raise NotImplementedError()
