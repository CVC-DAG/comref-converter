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
Helper classes for music semantic processing.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from fractions import Fraction
from functools import total_ordering
from math import ceil
from typing import TYPE_CHECKING, Any, Dict, List, NamedTuple, Optional, Tuple

from . import types as TT

if TYPE_CHECKING:
    from . import ast as AST

CLEF2SIGN = {
    TT.ClefType.CLEF_G: TT.NamedPitch.G,
    TT.ClefType.CLEF_C: TT.NamedPitch.C,
    TT.ClefType.CLEF_F: TT.NamedPitch.F,
    TT.ClefType.CLEF_PERCUSSION: TT.NamedPitch.G,
}


SYMBOL_TIMESIG_DUR = {
    TT.TimeSymbol.TS_COMMON: Fraction(4, 4) * 4,
    TT.TimeSymbol.TS_CUT: Fraction(2, 2) * 4,
}


@dataclass
class NotePitch:
    """Represents the pitch of a Note using CWMN semantics."""

    step: TT.NamedPitch
    octave: int
    alter: Fraction

    def __int__(self) -> int:
        """Convert the pitch into an absolute MIDI-like value.

        Returns
        -------
        int
            The real value of the pitch considering all of the possible notes in the
            keyboard range. Does not consider alterations.
        """
        return self.step.value + (len(TT.NamedPitch) * self.octave)

    def __sub__(
        self,
        val: int,
    ) -> NotePitch:
        """Subtract a fixed number of whole tones to the semantic pitch.

        Parameters
        ----------
        val : int
            The number of whole tones to subtract.

        Returns
        -------
        NotePitch
            A copy of the pitch with the modified attributes.
        """
        diff = self.step.value - val

        octaves = diff // len(TT.NamedPitch)
        new_pitch = diff % len(TT.NamedPitch)

        return NotePitch(TT.NamedPitch(new_pitch), self.octave - octaves, self.alter)

    def __add__(
        self,
        val: int,
    ) -> NotePitch:
        """Add a fixed number of whole tones to the semantic pitch.

        Parameters
        ----------
        val : int
            The number of whole tones to add.

        Returns
        -------
        NotePitch
            A copy of the pitch with the modified attributes.
        """
        diff = self.step.value + val

        octaves = diff // len(TT.NamedPitch)
        new_pitch = diff % len(TT.NamedPitch)

        return NotePitch(TT.NamedPitch(new_pitch), self.octave - octaves, self.alter)


@total_ordering
class StaffPosition(NamedTuple):
    """Represents the position of an element in a staff using MTN semantics.

    Uses a namedtuple instead of a dataclass for hashing purposes.
    """

    staff: int | None
    position: int | None  # None in any of these fields means anywhere.

    def __int__(self) -> int:
        """Convert the pitch into an absolute single value.

        Returns
        -------
        int
            A specific position determined by a single int value.
        """
        if self.staff is None:
            staff = 0
        else:
            staff = self.staff

        if self.position is None:
            position = 500
        else:
            position = self.position

        return 1000 * staff + position

    def __str__(self) -> str:
        """Convert staff position into a string."""
        staff = "ANY"
        position = "ANY"
        if self.staff is not None:
            staff = f"{self.staff:01}"
        if self.position is not None:
            position = f"{self.position:02}"
        return f"s:{staff}/p:{position}"

    def __eq__(self, value: object, /) -> bool:
        if not isinstance(value, StaffPosition):
            return False
        return int(self) == int(value)

    def __lt__(self, value: tuple[Any, ...], /) -> bool:
        if isinstance(value, StaffPosition):
            return int(self) < int(value)
        return False


def _compute_alterations() -> List[List[Optional[TT.AccidentalType]]]:
    has_alteration: List[List[Optional[TT.AccidentalType]]] = [
        [TT.AccidentalType.ACC_FLAT for _ in range(7)]
    ]
    mod_pitch = 3
    for _ in range(14):
        has_alteration.append(deepcopy(has_alteration[-1]))
        if has_alteration[-1][mod_pitch] is None:
            has_alteration[-1][mod_pitch] = TT.AccidentalType.ACC_SHARP
        elif has_alteration[-1][mod_pitch] == TT.AccidentalType.ACC_FLAT:
            has_alteration[-1][mod_pitch] = None

        mod_pitch = (mod_pitch + 4) % 7

    return has_alteration


def _compute_modifications() -> List[int]:
    return [((x * 4) + 3) % 7 for x in range(14)]


ACCIDENTAL_ALTER = {
    TT.AccidentalType.ACC_DOUBLE_FLAT: Fraction(-2, 1),
    TT.AccidentalType.ACC_DOUBLE_SHARP: Fraction(2, 1),
    TT.AccidentalType.ACC_FLAT: Fraction(-1, 1),
    TT.AccidentalType.ACC_SHARP: Fraction(1, 1),
    TT.AccidentalType.ACC_QUARTER_FLAT: Fraction(-1, 2),
    TT.AccidentalType.ACC_QUARTER_SHARP: Fraction(1, 2),
    TT.AccidentalType.ACC_NATURAL: Fraction(0, 1),
}

ACCIDENTAL_SUMMARISED = {
    k: "#" if ACCIDENTAL_ALTER[k] > 0 else "b" if ACCIDENTAL_ALTER[k] < 0 else " "
    for k in TT.AccidentalType
}


class MusicalKey:
    """Represents the key of a musical piece."""

    ALTERATIONS = _compute_alterations()
    MODIFICATION_SEQUENCE = _compute_modifications()

    SHARP_POSITIONS: Dict[Tuple[TT.NamedPitch, int], List[int]] = {
        (TT.NamedPitch.G, 4): [10, 7, 11, 8, 5, 9, 6],
        (TT.NamedPitch.F, 8): [8, 5, 9, 6, 3, 7, 4],
        (TT.NamedPitch.C, 2): [5, 9, 6, 10, 7, 11, 8],
        (TT.NamedPitch.C, 6): [9, 6, 10, 7, 4, 8, 5],
        (TT.NamedPitch.C, 8): [4, 8, 5, 9, 6, 10, 7],
    }

    FLAT_POSITIONS: Dict[Tuple[TT.NamedPitch, int], List[int]] = {
        (TT.NamedPitch.G, 4): [6, 9, 5, 8, 4, 7, 3],
        (TT.NamedPitch.F, 8): [4, 7, 3, 6, 2, 5, 1],
        (TT.NamedPitch.C, 2): [7, 10, 6, 9, 5, 8, 4],
        (TT.NamedPitch.C, 6): [5, 8, 4, 7, 3, 6, 2],
        (TT.NamedPitch.C, 8): [7, 10, 6, 9, 5, 8, 4],
    }

    def __init__(self, alters: List[float]) -> None:
        self.key = alters

    @classmethod
    def fifths_accidental_positions(
        cls,
        fifths: int,
        clef: AST.Clef,
    ) -> List[int]:
        """Compute accidental positions for a given clef and set of fifths.

        Parameters
        ----------
        fifths : int
            Number of fifths to alter in an unspecified direction.
        clef : AST.Clef
            The clef containing the staff information where the key is to be written.

        Returns
        -------
        List[int]
            List of positions for each accidental.
        """
        if fifths > 0:
            accidental_dict = cls.SHARP_POSITIONS
            direction = 1
        else:
            accidental_dict = cls.FLAT_POSITIONS
            direction = -1

        assert clef.position.position is not None
        assert clef.sign is not None
        try:
            return accidental_dict[(clef.sign, clef.position.position)][: abs(fifths)]
        except KeyError:
            ...

        accidentals = [
            clef.pitch2pos(
                NotePitch(
                    TT.NamedPitch(ii + (5 * direction) % len(TT.NamedPitch)),
                    clef.octave + direction,
                    Fraction(0),
                )
            )
            for ii in range(1, 8)
        ]
        return list(map(cls.ensure_range, accidentals))

    @classmethod
    def fifths_alterations(cls, fifths: int) -> List[Optional[TT.AccidentalType]]:
        """Get the alterations that would be produced on scale tones after x fifths.

        Parameters
        ----------
        fifths : int
            Number of fifths to move within the circle. Must be an integer between -7
            and 7.

        Returns
        -------
        List[Optional[TT.AccidentalType]]
            A list of length 7 where each element is a tone and its contents the
            required alterations. None means no alteration on that tone.
        """
        output: List[Optional[TT.AccidentalType]] = [
            None for _ in range(len(TT.NamedPitch))
        ]
        origin = 7
        target = origin + fifths
        if target < origin:
            origin, target = target, origin

        for alter in cls.MODIFICATION_SEQUENCE[origin:target]:
            output[alter] = (
                TT.AccidentalType.ACC_SHARP
                if fifths > 0
                else TT.AccidentalType.ACC_FLAT
            )
        return output

    @classmethod
    def ensure_range(cls, value: int) -> int:
        """Ensure the accidental is within the acceptable range of positions."""
        if value > 11:
            value -= 8 * ceil((value - 11) / 8)
        elif value < 1:
            value += 8 * ceil(-(value - 1) / 8)
        return value


DEFAULT_CLEF_POSITIONS = {
    TT.NamedPitch.G: 4,
    TT.NamedPitch.F: 8,
    TT.NamedPitch.C: 6,
}

DEFAULT_CLEF_OCTAVE = {
    TT.NamedPitch.G: 4,
    TT.NamedPitch.F: 3,
    TT.NamedPitch.C: 4,
}
