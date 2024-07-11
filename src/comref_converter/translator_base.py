"""The Common Optical Music Recognition Framework (COMReF) toolset.

Generic types for translator objects.

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

from abc import ABC, abstractmethod
from typing import Any, Set, Tuple

from .mtn import ast as AST

MeasureID = Tuple[str, str]


class Translator(ABC):
    """Interface defining methods for a translator."""

    @abstractmethod
    def translate(
        self,
        score_in: Any,
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
        MTN.AST.Score
            An object representing the score in MTN.
        """
        raise NotImplementedError

    @abstractmethod
    def reset(self) -> None:
        """Reset object to its default state."""
        raise NotImplementedError
