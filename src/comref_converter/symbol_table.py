"""The Common Optical Music Recognition Framework (COMReF) toolset.

Implements a symbol table to keep track of parsed elements.

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


from fractions import Fraction
from typing import Dict, List, Optional, Tuple

from .mtn import semantics as MS
from .mtn.types import TokenType

Identifier = int

GROUP_TOKENS = {
    TokenType.ARPEGGIATE,
    TokenType.BEAM,
    TokenType.GLISSANDO,
    TokenType.SLIDE,
    TokenType.SLUR,
    TokenType.TIED,
    TokenType.WAVY_LINE,
}


class SymbolTable:
    """A table keeping track of opened and closed symbols and identifiers."""

    def __init__(self) -> None:
        """Construct an empty SymbolTable."""
        # There has to be a beam stack for each combination of note types.
        self.beam_stacks: Dict[Tuple[bool, bool], List[int]] = {
            (cue, grace): [] for cue in [False, True] for grace in [False, True]
        }

        # For arpeggios. The relevant thing is that all arpeggios on the same chord
        # are the same object (thus, same time delta). Otherwise, consider the number.
        self.arpeggios: Dict[Tuple[Fraction, Optional[int]], Identifier] = {}

        # For slurs, slides, glissandos and wavy lines.
        self.point_to_point: Dict[Tuple[TokenType, Optional[int]], Identifier] = {}

        # For ties the position is needed and optionally their number
        self.ties: Dict[Tuple[MS.StaffPosition, Optional[int]], Identifier] = {}
        self._next_id: Identifier = 1

    def new_measure(self) -> None:
        """Set everything clean for a new measure."""
        self.arpeggios = {}

    def reset(self) -> None:
        """Set the symbol table back to the default state."""
        self.beam_stacks = {
            (cue, grace): [] for cue in {False, True} for grace in {False, True}
        }
        self.arpeggios = {}
        self.point_to_point = {}
        self.ties = {}
        self._next_id = 1

    def identify_beams(
        self,
        cue: bool,
        grace: bool,
        nbeams: int,
    ) -> List[Identifier]:
        """Provide a list of consistent IDs for ongoing beams.

        This should not be used in the scenario where there might be hooks. In that case
        just use the give identifier function directly (since they are self-contained).

        Parameters
        ----------
        cue : bool
            Whether it is a cue note that spawned the beam.
        grace : bool
            Whether it is a grace note that spawned the beam.
        nbeams : int
            Number of beams in the current stem that are not hooks.

        Returns
        -------
        List[Identifier]
            A list of identifiers to give to each beam.
        """
        beams = self.beam_stacks[(cue, grace)]

        if len(beams) < nbeams:
            for _ in range(nbeams - len(beams)):
                beams.append(self.give_identifier())
        elif len(beams) > nbeams:
            for _ in range(len(beams) - nbeams):
                beams.pop()

        return beams

    def identify_arpeggios(
        self,
        delta: Fraction,
        number: Optional[int],
    ) -> Identifier:
        """Provide an identifier to an arpeggio object.

        Parameters
        ----------
        delta : Fraction
            The time where the arpeggiated note is meant to play.
        number : Optional[int]
            A discerning number value to deambiguate multiple open arpeggios.

        Returns
        -------
        Identifier
            A unique identifier for the arpeggio object.
        """
        try:
            return self.arpeggios[(delta, number)]
        except KeyError:
            ident = self.give_identifier()
            self.arpeggios[(delta, number)] = ident
            return ident

    def identify_point_to_point(
        self,
        tok: TokenType,
        number: Optional[int],
    ) -> Identifier:
        """Provide a unique identifier to any start-stop type object.

        Parameters
        ----------
        tok : TokenType
            The type of music primitive to identify.
        number : Optional[int]
            A deambiguation number that can be optionally used.

        Returns
        -------
        Identifier
            A unique identifier for the object.
        """
        try:
            return self.point_to_point.pop((tok, number))
        except KeyError:
            ident = self.give_identifier()
            self.point_to_point[(tok, number)] = ident
            return ident

    def identify_tie(
        self,
        pitch: MS.StaffPosition,
        number: Optional[int],
    ) -> Identifier:
        """Provide a unique identifier to any tie object.

        Parameters
        ----------
        pitch : MS.StaffPosition
            The position on the staff of the note the tie is related to.
        number : Optional[int]
            A deambiguation number that can be optionally used.

        Returns
        -------
        Identifier
            A unique identifier for the object.
        """
        try:
            return self.ties.pop((pitch, number))
        except KeyError:
            ident = self.give_identifier()
            self.ties[(pitch, number)] = ident
            return ident

    def give_identifier(self) -> Identifier:
        """Provide an identifier to a symbol without registering it to the table."""
        identifier = self._next_id
        self._next_id += 1

        return identifier
