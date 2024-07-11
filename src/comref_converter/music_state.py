"""The Common Optical Music Recognition Framework (COMReF) toolset.

Implementation of a music state keeping class.

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

from copy import deepcopy
from fractions import Fraction
from typing import List, Optional, Tuple

from sortedcontainers import SortedDict

from . import symbol_table as ST
from .mtn import ast as AST


class ScoreState:
    """Contain the state of a single part of the score."""

    def __init__(self) -> None:
        self.nstaves = 1
        self.divisions = 1
        self.current_time = Fraction(0)
        self.time_buffer: Fraction = Fraction(0)

        # The initial state for a measure. Posterior attributes are computed by
        # composing these initial attributes with a stack of saved attribute elements.
        self.initial_attributes: AST.Attributes = AST.Attributes.make_empty(
            self.nstaves, self.current_time, True
        )

        # The attributes at the current time step (composing the initial state with
        # the stack of states).
        self.current_attributes: AST.Attributes = self.initial_attributes.copy()

        self.stack: SortedDict[Fraction, AST.Attributes] = SortedDict()

    def __str__(self) -> str:
        """Get simple representation for debugging purposes."""
        return (
            f"========= STATE =========\nStaves: {self.nstaves}\nDivisions:"
            f" {self.divisions}\nTime: {self.current_time}\nBuffer:"
            f" {self.time_buffer}\n{str(self.attributes)}\nStack:\n"
        ) + "\n - - -\n".join(
            map(
                lambda x: f"({x[0]}) Delta {str(x[1][0])}: {x[1][0]}",
                enumerate(self.stack.items()),
            )
        )

    def __repr__(self) -> str:
        """Get simple representation for debugging purposes."""
        return str(self)

    @property
    def attributes(self) -> AST.Attributes:
        """Get the current attributes of the score."""
        return self.current_attributes

    @attributes.setter
    def attributes(
        self,
        attributes: AST.Attributes,
    ) -> None:
        """Update the attributes of the score.

        Parameters
        ----------
        attributes : AST.Attributes
            Attributes object currently in use.
        """
        if self.current_time in self.stack:
            self.stack[self.current_time].merge(attributes)
        else:
            self.stack[self.current_time] = attributes

        self.current_attributes.merge(attributes)

    @property
    def attribute_list(self) -> List[AST.Attributes]:
        return list(self.stack.values())

    def increment_time(self, increment: Fraction) -> None:
        """Move the internal time by a set increment (positive or negative).

        Parameters
        ----------
        increment : Fraction
            Amount of fractions of a step to change timer by.
        """
        self.move_buffer()
        target_time = self.current_time + increment
        self.change_time(target_time)

    def change_time(self, time: Fraction) -> None:
        """Move the internal timer and update the state accordingly.

        It goes through every state change within the measure, but given that attribute
        nodes should be a rather rare occurrence anyway for the time being this naive
        approach should be enough.

        Parameters
        ----------
        time : Fraction
            What time to move the state to.
        """
        if time < self.current_time:
            if len(self.stack) > 0:
                index = self.stack.bisect_left(time + Fraction(1, 32782))
                self.current_attributes = self.initial_attributes.copy()

                for intermediate in self.stack.keys()[:index]:
                    self.current_attributes.merge(self.stack[intermediate])
        else:
            if len(self.stack) > 0:
                right_index = self.stack.bisect_left(time + Fraction(1, 32782))
                left_index = self.stack.bisect_right(time - Fraction(1, 32782))

                for intermediate in self.stack.keys()[left_index:right_index]:
                    self.current_attributes.merge(self.stack[intermediate])

        self.current_time = time
        self.time_buffer = Fraction(0)

    def set_buffer(self, buffer: Fraction) -> None:
        """Set a value for the time buffer.

        The time buffer is the amount of time that will pass on the next call to
        move_buffer. This is used to account for chords when parsing nodes in succession
        from a MXML file.

        Parameters
        ----------
        buffer : Fraction
            Number of fractions of a beat to move the time by.
        """
        self.move_buffer()
        self.time_buffer = buffer

    def move_buffer(self) -> None:
        """Update the current time with the buffer and reset the latter."""
        if self.time_buffer != Fraction(0):
            new_time = self.current_time + self.time_buffer
            self.change_time(new_time)

    def change_staves(self, nstaves: int) -> None:
        """Change the current number of staves within the score.

        Parameters
        ----------
        nstaves : int
            The number of staves to change the part to.
        """
        assert self.current_time == Fraction(0), "Changing number of staves mid-measure"
        assert len(self.stack) == 0, "Changing number of staves mid-measure"

        self.initial_attributes.change_staves(nstaves, True)
        self.current_attributes = self.initial_attributes.copy()

        self.nstaves = nstaves

    def new_measure(self) -> None:
        """Start a new measure keeping the same attributes as the last."""
        if len(self.stack) > 0:
            self.change_time(self.stack.peekitem(0)[0])
            self.change_time(self.stack.peekitem(-1)[0])
        self.initial_attributes = self.current_attributes
        self.current_attributes = self.initial_attributes.copy()

        self.stack = SortedDict()

        self.current_time = Fraction(0)
        self.time_buffer = Fraction(0)

    def start_attributes(self, remove_timesig: bool = True) -> AST.Attributes:
        """Return the attributes at the beginning of the measure."""
        initial = self.initial_attributes.copy()
        if Fraction(0) in self.stack:
            initial.merge(self.stack[Fraction(0)])

        # The time signature is not needed, but in case this method can be reused
        if remove_timesig:
            for ii in initial.timesig.keys():
                initial.timesig[ii] = None
        return initial

    def get_duration(self) -> Fraction:
        """Get the duration of a measure. Raises if not available."""
        try:
            timesig_obj = next(
                x for x in self.attributes.timesig.values() if x is not None
            )
        except StopIteration:
            raise ValueError("No time semantics available for the current state")
        return timesig_obj.time_value
