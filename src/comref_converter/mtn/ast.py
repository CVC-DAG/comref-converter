"""The Common Optical Music Recognition Framework (COMReF) toolset.

Implementation of the MTN format classes and basic operations.

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

import re
from abc import ABC, abstractmethod
from fractions import Fraction
from functools import total_ordering
from typing import (Any, Dict, Generator, List, NamedTuple, Optional, Sequence,
                    Type, Union, cast)

from . import semantics as MS
from . import types as TT


class Visitor(ABC):
    """Base class for ast visitors for transformation and navigation of mtn notation."""

    @abstractmethod
    def visit_ast(self, root: SyntaxNode) -> Any:
        """Perform visiting operation."""
        return None

    @abstractmethod
    def visit_score(self, score: Score) -> Any:
        """Perform visiting operation on Score node."""
        return None

    @abstractmethod
    def visit_note(self, note: Note) -> Any:
        """Perform visiting operation on Note node."""
        raise NotImplementedError

    @abstractmethod
    def visit_toplevel(self, toplevel: TopLevel) -> Any:
        """Perform visiting operation on TopLevel node."""
        raise NotImplementedError

    @abstractmethod
    def visit_token(self, token: Token) -> Any:
        """Perform visiting operation on Token node."""
        raise NotImplementedError

    @abstractmethod
    def visit_chord(self, chord: Chord) -> Any:
        """Perform visiting operation on Chord node."""
        raise NotImplementedError

    @abstractmethod
    def visit_rest(self, rest: Rest) -> Any:
        """Perform visiting operation on Rest node."""
        raise NotImplementedError

    @abstractmethod
    def visit_note_group(self, note_group: NoteGroup) -> Any:
        """Perform visiting operation on NoteGroup node."""
        raise NotImplementedError

    @abstractmethod
    def visit_attributes(self, attributes: Attributes) -> Any:
        """Perform visiting operation on Attributes node."""
        raise NotImplementedError

    @abstractmethod
    def visit_time_signature(self, time_signature: TimeSignature) -> Any:
        """Perform visiting operation on TimeSignature node."""
        raise NotImplementedError

    @abstractmethod
    def visit_key(self, key: Key) -> Any:
        """Perform visiting operation on Key node."""
        raise NotImplementedError

    @abstractmethod
    def visit_clef(self, clef: Clef) -> Any:
        """Perform visiting operation on Clef node."""
        raise NotImplementedError

    @abstractmethod
    def visit_direction(self, direction: Direction) -> Any:
        """Perform visiting operation on Direction node."""
        raise NotImplementedError

    @abstractmethod
    def visit_measure(self, measure: Measure) -> Any:
        """Perform visiting operation on Measure node."""
        raise NotImplementedError

    @abstractmethod
    def visit_barline(self, barline: Barline) -> Any:
        """Perform visiting operation on Barline node."""
        raise NotImplementedError

    @abstractmethod
    def visit_tuplet(self, tuplet: Tuplet) -> Any:
        """Perform visiting operation on Tuplet node."""
        raise NotImplementedError

    @abstractmethod
    def visit_numerator(self, numerator: Numerator) -> Any:
        """Perform visiting operation on Numerator node."""
        raise NotImplementedError

    @abstractmethod
    def visit_denominator(self, denominator: Denominator) -> Any:
        """Perform visiting operation on Denominator node."""
        raise NotImplementedError

    @abstractmethod
    def visit_number(self, number: Number) -> Any:
        """Perform visiting operation on Number node."""
        raise NotImplementedError

    @abstractmethod
    def visit_timesig_fraction(self, fraction: TimesigFraction) -> Any:
        """Perform visiting operation on timesig fraction node."""
        raise NotImplementedError


class SyntaxNode(ABC):
    """Interface for visitable types within the MTN AST."""

    # TODO: Maybe this makes things a bit easier. In order to do it however I need to
    # change attributes to lists (which makes sense, since staff identifiers are
    # always contiguous, the only annoying thing is the off-by-one error from MusicXML
    # identifiers starting from 1).
    #
    # def __init__(self) -> None:
    #     super().__init__()
    #     self.__child_nodes = []

    @abstractmethod
    def accept(self, visitor: Visitor) -> Any:
        """Have visitor perform operation on node."""
        raise NotImplementedError

    @abstractmethod
    def compare(self, other: SyntaxNode) -> bool:
        """Compare two elements for equality of contents. Calls recursively."""
        raise NotImplementedError

    @abstractmethod
    def compare_raise(self, other: SyntaxNode) -> None:
        """Compare two elements for equality of contents. Raises on false."""
        if not isinstance(other, type(self)):
            raise TypeError(
                f"Type of produced object ({type(other)}) is different than expected ({type(self)})"
            )

    @staticmethod
    def _compare_lists(
        base: Sequence[SyntaxNode],
        other: Sequence[SyntaxNode],
        raises: bool = False,
    ) -> bool:
        if not len(base) == len(other):
            if raises:
                raise ValueError(
                    f"Length of produced sequence ({len(other)}) is different than expected ({len(base)})"
                )
        if raises:
            return all(
                map(
                    lambda x: x[0].compare_raise(x[1]),
                    zip(base, other),
                )
            )
        else:
            return all(
                map(
                    lambda x: x[0].compare(x[1]),
                    zip(base, other),
                )
            )

    @staticmethod
    def _compare_maybe(
        base: Optional[SyntaxNode],
        other: Optional[SyntaxNode],
        raises: bool = False,
    ) -> bool:
        if base is not None and other is not None:
            if raises:
                base.compare_raise(other)
                return True
            else:
                if not base.compare(other):
                    return False
        elif not (base is None and other is None):
            if raises:
                raise ValueError(
                    f"The generated object is {other} when it should be {base}"
                )
            return False
        return True

    # def iter_children(self) -> Generator[SyntaxNode]:
    #     yield self

    #     for child in self.__child_nodes:
    #         if isinstance(SyntaxNode, child):
    #             yield from child.iter_children()
    #         elif isinstance(list, child):
    #             for ch2 in child:
    #                 yield ch2

    # def register_children(self, *args) -> None:
    #     for arg in args:
    #         self.__child_nodes.append(arg)


class TopLevel(SyntaxNode):
    """Represent any element that lies within a music measure."""

    def __init__(self, delta: Fraction) -> None:
        super().__init__()
        self.delta = delta

    def __lt__(self, other: TopLevel) -> bool:
        """Compare two toplevel elements and see which one takes precedence."""
        if self.delta < other.delta:
            return True
        elif self.delta > other.delta:
            return False

        self_precedence = _OBJECT_PRECEDENCE[type(self)]
        other_precedence = _OBJECT_PRECEDENCE[type(other)]

        if self_precedence < other_precedence:
            return True
        elif self_precedence > other_precedence:
            return False

        if self.position() < other.position():
            return True
        return False

    def __eq__(self, other: object) -> bool:
        """Compare two toplevel elements and see which one takes precedence."""
        if not isinstance(other, TopLevel):
            return False

        if self.delta != other.delta:
            return False

        self_precedence = _OBJECT_PRECEDENCE[type(self)]
        other_precedence = _OBJECT_PRECEDENCE[type(other)]

        if self_precedence != other_precedence:
            return False

        if self.position() != other.position():
            return False
        return True

    def position(self) -> MS.StaffPosition:
        return MS.StaffPosition(None, None)

    def accept(self, visitor: Visitor) -> Any:
        """Have visitor perform operation on node."""
        return visitor.visit_toplevel(self)

    def compare_raise(self, other: SyntaxNode) -> None:
        super().compare_raise(other)

        if not isinstance(other, TopLevel):
            raise TypeError("Other object is not TopLevel - no delta value")

        if self.delta != other.delta:
            raise ValueError(
                f"Expected delta value of {str(self.delta)} but got {str(other.delta)} instead."
            )


class BoundingBox(NamedTuple):
    """Orthonormal box spanning the outline of the object."""

    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def x(self):
        """Get x coordinate of the center of the bounding box."""
        return (self.x2 - self.x1) // 2

    @property
    def y(self):
        """Get y coordinate of the center of the bounding box."""
        return (self.y2 - self.y1) // 2


class Token(SyntaxNode):
    """Represents a single object instance within the ast."""

    def __init__(
        self,
        token_type: TT.TokenType,
        modifiers: Dict[str, Any],
        position: MS.StaffPosition,
        token_id: int,
        token_coords: BoundingBox | None = None,
    ) -> None:
        super().__init__()

        self.token_type = token_type
        self.modifiers = modifiers
        self.position = position
        self.token_id = token_id

        self.coordinates = token_coords

    def __str__(self) -> str:
        """Quick representation of the token for debugging."""
        output = self.token_type.value
        key_names = sorted(self.modifiers.keys())
        mods = self.modifiers
        modifiers = "_".join(
            [
                k if not hasattr(mods[k], "value") else str(mods[k].value)
                for k in key_names
            ]
        )

        return output + ("_" * (len(modifiers) > 0)) + modifiers

    def __repr__(self) -> str:
        """Quick representation of the token for debugging."""
        return str(self)

    def accept(self, visitor: Visitor) -> Any:
        """Have visitor perform operation on node."""
        return visitor.visit_token(self)

    def compare(self, other: SyntaxNode) -> bool:
        if not isinstance(other, Token):
            return False
        return (
            self.token_type == other.token_type
            and self.position == other.position
            and self.modifiers == other.modifiers
        )

    def compare_raise(self, other: SyntaxNode) -> None:
        super().compare_raise(other)
        other = cast(Token, other)

        if self.token_type != other.token_type:
            raise ValueError(f"Expected token type {type(self)} but got {type(other)}")

        if self.position != other.position:
            raise ValueError(
                f"Expected token position {str(self.position)} but got {str(other.position)}"
            )

        if self.modifiers != other.modifiers:
            raise ValueError(
                f"Expected token modifiers to be: \n"
                f"{' '.join(self.modifiers.values())}"
                f" but got Expected token modifiers to be: \n"
                f"{' '.join(other.modifiers.values())}"
            )


class Note(SyntaxNode):
    """Represents all tokens related to a single note."""

    def __init__(
        self,
        notehead: Token,
        dots: List[Token],
        accidentals: List[Token],
        modifiers: List[Token | Tuplet],
        parent: Optional[Chord] = None,
    ) -> None:
        super().__init__()

        self.notehead = notehead
        self.dots = dots
        self.accidentals = accidentals
        self.modifiers = modifiers
        self.parent = parent

    def __str__(self) -> str:
        """Quick representation of a note for debugging."""
        return (
            f"Note @{str(self.notehead.position)}: {str(self.notehead)} with "
            f"{len(self.dots)} dots, "
            f"{len(self.accidentals)} accidentals and {len(self.modifiers)} modifiers."
        )

    def __repr__(self) -> str:
        """Quick representation of the token for debugging."""
        return str(self)

    def accept(self, visitor: Visitor) -> Any:
        """Have visitor perform operation on node."""
        return visitor.visit_note(self)

    def compare(self, other: SyntaxNode) -> bool:
        if not isinstance(other, Note):
            return False
        if not self.notehead.compare(other.notehead):
            return False

        return (
            self._compare_lists(self.dots, other.dots)
            and self._compare_lists(self.accidentals, other.accidentals)
            and self._compare_lists(self.modifiers, other.modifiers)
        )

    def compare_raise(self, other: SyntaxNode) -> None:
        super().compare_raise(other)
        other = cast(Note, other)

        self.notehead.compare_raise(other.notehead)
        self._compare_lists(self.dots, other.dots, True)
        self._compare_lists(self.accidentals, other.accidentals, True)
        self._compare_lists(self.modifiers, other.modifiers, True)

    def position(self) -> MS.StaffPosition:
        """Get position of the note for in-chord sorting."""
        return self.notehead.position

    def get_pitch(self) -> MS.StaffPosition:
        """Get position of the current note."""
        return self.notehead.position

    def get_delta(self) -> Optional[Fraction]:
        """Get the time from the start of the measure for this note."""
        if self.parent is not None:
            return self.parent.delta
        return None


class Chord(SyntaxNode):
    """Represents a set of notes playing together at the same time."""

    def __init__(
        self,
        delta: Fraction,
        stem: Optional[Token],
        notes: List[Note],
    ) -> None:
        super().__init__()

        assert len(notes) > 0, "Chord without notes."
        self.delta = delta
        self.stem = stem
        self.notes = notes

        for note in self.notes:
            note.parent = self

    def __str__(self) -> str:
        """Quick representation of a chord for debugging."""
        return f"Stem: {str(self.stem)}\n" + "\n".join(map(str, self.notes))

    def __repr__(self) -> str:
        """Quick representation of the token for debugging."""
        return str(self)

    def __lt__(self, other: Chord) -> bool:
        return self.delta < other.delta

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Chord):
            return False
        return self.delta == other.delta

    def accept(self, visitor: Visitor) -> Any:
        """Have visitor perform operation on node."""
        return visitor.visit_chord(self)

    def compare(self, other: SyntaxNode) -> bool:
        if not isinstance(other, Chord):
            return False

        if not self._compare_maybe(self.stem, other.stem):
            return False

        if not self.delta == other.delta:
            return False

        return self._compare_lists(self.notes, other.notes)

    def compare_raise(self, other: SyntaxNode) -> None:
        super().compare_raise(other)
        other = cast(Chord, other)

        self._compare_maybe(self.stem, other.stem, True)
        self._compare_lists(self.notes, other.notes, True)

    def add_note(self, note: Note) -> None:
        """Add a note sorted MTN-wise to the chord.

        Parameters
        ----------
        note : Note
            The note to add to the chord.
        """
        note.parent = self
        self.notes.append(note)
        self.notes.sort(key=lambda x: int(x.notehead.position))

    def get_first_note(self) -> Note:
        """Return the first note in the chord."""
        if len(self.notes) == 0:
            raise ValueError("Chord should have at least one note.")
        return self.notes[0]

    def position(self) -> MS.StaffPosition:
        return self.get_first_note().position()

    def is_stem_upwards(self) -> bool:
        if self.stem is None:
            return False
        if "type" not in self.stem.modifiers:
            raise ValueError("Invalid stem without a type")

        return self.stem.modifiers["type"] == TT.StemDirection.UP


class Rest(TopLevel):
    """Represents a rest within the score."""

    RE_NOTETYPE = re.compile(r"rest_(.*)")

    def __init__(
        self,
        delta: Fraction,
        rest_token: Token,
        dots: List[Token],
        modifiers: List[Token | Tuplet],
    ) -> None:
        """Represent a Rest in the MTN hierarchy.

        Parameters
        ----------
        delta : Fraction
            Fractions of a beat since the beginning of the measure.
        rest_token : PositionAwareToken
            The token representing the underlying rest object. It must include the
            rest type as a semantic indicator, which belongs to the NoteType enum.
        dots : List[Token]
            List of dot tokens.
        modifiers : List[Token]
            Additional objects modifying the semantics of the rest.
        """
        super().__init__(delta)

        self.rest_token = rest_token
        self.dots = dots
        self.modifiers = modifiers

        self.rest_type = self.rest_token.modifiers["type"]

    def __str__(self) -> str:
        """Quick representation of a rest for debugging."""
        return f"Rest (Delta {self.delta}): {str(self.rest_token)}"

    def __repr__(self) -> str:
        """Quick representation of the token for debugging."""
        return str(self)

    def accept(self, visitor: Visitor) -> Any:
        """Have visitor perform operation on node."""
        return visitor.visit_rest(self)

    def compare(self, other: SyntaxNode) -> bool:
        if not isinstance(other, Rest):
            return False

        if not self.delta == other.delta:
            return False

        if not self.rest_token.compare(other.rest_token):
            return False

        return self._compare_lists(self.dots, other.dots) and self._compare_lists(
            self.modifiers, other.modifiers
        )

    def compare_raise(self, other: SyntaxNode) -> None:
        super().compare_raise(other)
        other = cast(Rest, other)

        self.rest_token.compare_raise(other.rest_token)
        self._compare_lists(self.dots, other.dots, True)
        self._compare_lists(self.modifiers, other.modifiers, True)

    def get_pitch(self) -> MS.StaffPosition:
        """Get position of the current rest."""
        return self.rest_token.position

    def get_delta(self) -> Optional[Fraction]:
        """Get the time from the start of the measure for this note."""
        return self.delta

    def position(self) -> MS.StaffPosition:
        return self.rest_token.position


class NoteGroup(TopLevel):
    """Represents a joint set of notes within the score."""

    def __init__(
        self,
        delta: Fraction,
        chords_or_groups: List[Union[Chord, NoteGroup]],
        beams_or_flags: List[Token],
    ) -> None:
        super().__init__(delta)

        self.children = chords_or_groups
        self.appendages = beams_or_flags

    def __str__(self) -> str:
        """Quick representation of a NoteGroup for debugging."""
        return f"Note Group (Delta {self.delta}):" + "\n\t".join(
            map(str, self.children)
        )

    def __repr__(self) -> str:
        """Quick representation of the token for debugging."""
        return str(self)

    def __lt__(self, other: TopLevel) -> bool:
        """Compare two toplevel elements and see which one takes precedence."""
        prev = super().__lt__(other)
        if not isinstance(other, NoteGroup) or prev:
            return prev

        if (
            self.delta == other.delta
            and _OBJECT_PRECEDENCE[type(self)] == _OBJECT_PRECEDENCE[type(other)]
            and self.position == other.position()
        ):
            if other.get_first_chord().is_stem_upwards():
                return True
            return False
        else:
            return prev

    def __eq__(self, other: object) -> bool:
        """Compare two toplevel elements and see which one takes precedence."""
        if not isinstance(other, TopLevel):
            return False
        prev = super().__eq__(other)

        if not isinstance(other, NoteGroup) or not prev:
            return prev

        if not (
            self.get_first_chord().is_stem_upwards()
            and other.get_first_chord().is_stem_upwards()
        ):
            return False

        return True

    def position(self) -> MS.StaffPosition:
        return self.get_first_chord().position()

    def accept(self, visitor: Visitor) -> Any:
        """Have visitor perform operation on node."""
        return visitor.visit_note_group(self)

    def compare(self, other: SyntaxNode) -> bool:
        if not isinstance(other, NoteGroup):
            return False

        if not self.delta == other.delta:
            return False

        return self._compare_lists(
            self.children, other.children
        ) and self._compare_lists(self.appendages, other.appendages)

    def compare_raise(self, other: SyntaxNode) -> None:
        super().compare_raise(other)
        other = cast(NoteGroup, other)

        self._compare_lists(self.children, other.children, True)
        self._compare_lists(self.appendages, other.appendages, True)

    def merge(self, other: NoteGroup) -> NoteGroup:
        """Merge two NoteGroups together."""
        self.children += other.children
        self.appendages += other.appendages

        return self

    def absorb(self, other: NoteGroup) -> NoteGroup:
        """Absorb a child node."""
        self.children = other.children
        self.appendages += other.appendages

        return self

    def simplify(self) -> None:
        """Reduce nesting of the NoteGroup."""
        for child in self.children:
            if isinstance(child, NoteGroup):
                child.simplify()

        if len(self.children) == 1 and isinstance(self.children[0], NoteGroup):
            self.absorb(self.children[0])

    def get_first_chord(self) -> Chord:
        """Return the first chord in a NoteGroup (regardless of how deeply nested)."""
        if isinstance(self.children[0], Chord):
            return self.children[0]
        else:
            return self.children[0].get_first_chord()


class Tuplet(SyntaxNode):
    """Represents a set of objects subject to a tuple."""

    def __init__(
        self,
        number: Optional[Number],
        tuplet: Token,
    ) -> None:
        self.number = number
        self.tuplet = tuplet

    def __str__(self) -> str:
        """Quick representation of a NoteGroup for debugging."""
        return f"Tuplet: {str(self.tuplet)} | {str(self.number)}"

    def __repr__(self) -> str:
        """Quick representation of the token for debugging."""
        return str(self)

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit_tuplet(self)

    def compare(self, other: SyntaxNode) -> bool:
        if not isinstance(other, Tuplet):
            return False

        if not self._compare_maybe(self.number, other.number):
            return False

        return self.tuplet.compare(other.tuplet)

    def compare_raise(self, other: SyntaxNode) -> None:
        super().compare_raise(other)
        other = cast(Tuplet, other)

        self._compare_maybe(self.number, other.number)
        self.tuplet.compare(other.tuplet)


class Attributes(TopLevel):
    """Represents a joint set of attributes within the score."""

    def __init__(
        self,
        delta: Fraction,
        nstaves: int,
        key: Dict[int, Key | None],
        clef: Dict[int, Clef | None],
        timesig: Dict[int, TimeSignature | None],
    ) -> None:
        """Construct attributes change object.

        Parameters
        ----------
        delta : Fraction
            Amount of time since the start of the bar.
        nstaves: int
            Number of staves this object encapsulates.
        key : Dict[int, Key | None]
            Set of objects representing a key change. A dict that maps a staff with its
            key signature change, if applicable (otherwise None).
        clef : Dict[int, Clef | None]
            Dictionary mapping the staff id with the objects related to the underlying
            clef change. Maps to none for those staves where there is no change.
        timesig : Dict[int, TimeSignature | None]
            Set of objects representing a time signature change. A dict that maps a
            staff with its time signature, if applicable (otherwise None).
        """
        super().__init__(delta)
        self.nstaves = nstaves

        assert (
            len(key) == nstaves and len(clef) == nstaves and len(timesig) == nstaves
        ), "Uneven number of staves in attribute object."

        self.key = key
        self.clef = clef
        self.timesig = timesig

    def __str__(self) -> str:
        """Quick representation of a clef for debugging."""
        return (
            f"Attributes (Delta {self.delta}): \n\t{str(self.key)}\n\t{str(self.clef)}"
            f"\n\t{str(self.timesig)}"
        )

    def __repr__(self) -> str:
        """Quick representation of the token for debugging."""
        return str(self)

    def copy(self) -> Attributes:
        # Written like this to ensure that the dictionaries are not soft copies of the
        # previous ones
        return Attributes(
            self.delta,
            self.nstaves,
            {k: v for k, v in self.key.items()},
            {k: v for k, v in self.clef.items()},
            {k: v for k, v in self.timesig.items()},
        )

    def merge(self, other: Attributes) -> None:
        """Combine the contents of two attribute objects into the current one.

        It prioritises the defaults from the caller but overrides anything that is not
        None in the other object.

        Parameters
        ----------
        other : Attributes
            An attributes object to merge with the current one.
        """
        assert (
            self.nstaves == other.nstaves
        ), "Merging attributes with different number of staves"

        self.delta = other.delta

        self.key = self._merge_dict(self.key, other.key)
        self.clef = self._merge_dict(self.clef, other.clef)
        self.timesig = self._merge_dict(self.timesig, other.timesig)

    @staticmethod
    def _merge_dict(
        origin: Dict[int, Optional[Any]],
        target: Dict[int, Optional[Any]],
    ) -> Dict[int, Optional[Any]]:
        return {
            key: target.get(key, None) or origin.get(key, None)
            for key in sorted(origin.keys() | target.keys())
        }

    def accept(self, visitor: Visitor) -> Any:
        """Have visitor perform operation on node."""
        return visitor.visit_attributes(self)

    def compare(self, other: SyntaxNode) -> bool:
        # FIXME: This is getting spaghettier and spaghettier. Improve types.
        if not isinstance(other, Attributes):
            return False

        if not (self.delta == other.delta and self.nstaves == other.nstaves):
            return False

        self_keys = [x for x in self.key.values() if x is not None]
        other_keys = [x for x in other.key.values() if x is not None]

        return (
            (
                self._compare_lists(self_keys, other_keys)
                or (
                    len([y for x in self_keys for y in x.accidentals + x.naturals]) == 0
                    and len([y for x in other_keys for y in x.accidentals + x.naturals])
                    == 0
                )
            )
            and self._compare_lists(
                [x for x in self.clef.values() if x is not None],
                [x for x in other.clef.values() if x is not None],
            )
            and self._compare_lists(
                [x for x in self.timesig.values() if x is not None],
                [x for x in other.timesig.values() if x is not None],
            )
        )

    def compare_raise(self, other: SyntaxNode) -> None:
        super().compare_raise(other)
        other = cast(Attributes, other)

        self_keys = [x for x in self.key.values() if x is not None]
        other_keys = [x for x in other.key.values() if x is not None]

        try:
            self._compare_lists(self_keys, other_keys, True)
        except ValueError:
            if not (
                len([y for x in self_keys for y in x.accidentals + x.naturals]) == 0
                and len([y for x in other_keys for y in x.accidentals + x.naturals])
                == 0
            ):
                raise
        self._compare_lists(
            [x for x in self.clef.values() if x is not None],
            [x for x in other.clef.values() if x is not None],
            True,
        )
        self._compare_lists(
            [x for x in self.timesig.values() if x is not None],
            [x for x in other.timesig.values() if x is not None],
            True,
        )

    @classmethod
    def make_empty(
        cls,
        nstaves: int,
        delta: Fraction,
        init_default: bool = False,
    ) -> Attributes:
        """Empty attributes object at current time and with known number of staves.

        Parameters
        ----------
        nstaves : int
            Number of staves of the current measure.
        delta : Fraction
            Time position of the current Attributes object.

        Returns
        -------
        AST.Attributes
            Empty attributes object at current time.
        """
        key: Dict[int, Optional[Key]] = {
            staff: Key.default_key() if init_default else None
            for staff in range(1, nstaves + 1)
        }
        timesig: Dict[int, Optional[TimeSignature]] = {
            staff: TimeSignature.default_timesig() if init_default else None
            for staff in range(1, nstaves + 1)
        }
        clef: Dict[int, Optional[Clef]] = {
            staff: Clef.default_clef(staff) if init_default else None
            for staff in range(1, nstaves + 1)
        }

        return Attributes(delta, nstaves, key, clef, timesig)

    def change_staves(self, nstaves: int, init_default: bool) -> None:
        if nstaves > self.nstaves:
            for ii in range(self.nstaves + 1, nstaves + 1):
                self.clef[ii] = Clef.default_clef(ii) if init_default else None
                self.key[ii] = Key.default_key() if init_default else None
                self.timesig[ii] = (
                    TimeSignature.default_timesig() if init_default else None
                )
        else:
            self.clef = {ii: clef for ii, clef in self.clef.items() if ii <= nstaves}
            self.key = {ii: key for ii, key in self.key.items() if ii <= nstaves}
            self.timesig = {
                ii: timesig for ii, timesig in self.timesig.items() if ii <= nstaves
            }
        self.nstaves = nstaves

    def set_clef(self, clef: Clef, staff: int) -> None:
        assert (staff - 1) < self.nstaves, "Attempting write clef on non-existing staff"
        self.clef[staff] = clef

    def set_timesig(self, timesig: TimeSignature, staff: int) -> None:
        assert (staff - 1) < self.nstaves, "Attempting write time on non-existing staff"

        self.timesig[staff] = timesig

    def set_key(self, key: Key, staff: int) -> None:
        assert (staff - 1) < self.nstaves, "Attempting write key on non-existing staff"
        self.key[staff] = key

    def get_clef(self, staff: int) -> Optional[Clef]:
        assert (staff - 1) < self.nstaves, "Attempting fetch key on non-existing staff"
        return self.clef[staff]

    def get_timesig(self, staff: int) -> Optional[TimeSignature]:
        assert (staff - 1) < self.nstaves, "Attempting fetch time on non-existing staff"
        return self.timesig[staff]

    def get_key(self, staff: int) -> Optional[Key]:
        assert (staff - 1) < self.nstaves, "Attempting fetch time on non-existing staff"
        return self.key[staff]


class TimeSignature(SyntaxNode):
    """Represents a time signature within the score."""

    def __init__(
        self,
        time_symbol: Optional[Token],
        compound_time_signature: Optional[List[Union[TimesigFraction, Token]]],
        time_value: Fraction,
    ) -> None:
        super().__init__()
        self.time_symbol = time_symbol
        self.compound_time_signature = compound_time_signature
        self.time_value = time_value

        assert not (
            self.time_symbol is not None and self.compound_time_signature is not None
        ), "Time signature with mixed types."

    def __str__(self) -> str:
        """Quick representation of a timesig for debugging."""
        return f"Time: {str(self.time_value)}"

    def __repr__(self) -> str:
        """Quick representation of the token for debugging."""
        return str(self)

    def accept(self, visitor: Visitor) -> Any:
        """Have visitor perform operation on node."""
        return visitor.visit_time_signature(self)

    def compare(self, other: SyntaxNode) -> bool:
        if not isinstance(other, TimeSignature):
            return False

        if not self.time_value == other.time_value:
            return False

        self._compare_maybe(self.time_symbol, other.time_symbol)

        if (
            self.compound_time_signature is not None
            and other.compound_time_signature is not None
        ):
            return self._compare_lists(
                self.compound_time_signature, other.compound_time_signature
            )
        elif not (self.time_symbol is None and other.time_symbol is None):
            return False
        return True

    def compare_raise(self, other: SyntaxNode) -> None:
        super().compare_raise(other)
        other = cast(TimeSignature, other)

        if not self.time_value == other.time_value:
            raise ValueError(
                f"Time value of time signature ({other.time_value}) is different "
                f"than base ({self.time_value})"
            )
        if (
            self.compound_time_signature is not None
            and other.compound_time_signature is not None
        ):
            self._compare_lists(
                self.compound_time_signature, other.compound_time_signature, True
            )
        self._compare_maybe(self.time_symbol, other.time_symbol, True)

    @classmethod
    def default_timesig(cls) -> TimeSignature:
        return TimeSignature(None, None, Fraction(4, 1))


class TimesigFraction(SyntaxNode):
    """Represents a compound time signature numerator."""

    def __init__(
        self,
        numerator: Numerator,
        denominator: Optional[Denominator],
    ) -> None:
        super().__init__()
        self.numerator = numerator
        self.denominator = denominator

    def __str__(self) -> str:
        """Quick representation of the numerator for debugging."""
        return f"({str(self.numerator)}/{str(self.denominator)})"

    def __repr__(self) -> str:
        """Quick representation of the token for debugging."""
        return str(self)

    def accept(self, visitor: Visitor) -> Any:
        """Have visitor perform operation on node."""
        return visitor.visit_timesig_fraction(self)

    def compare(self, other: SyntaxNode) -> bool:
        if not isinstance(other, TimesigFraction):
            return False

        if not self.numerator.compare(other.numerator):
            return False

        return self._compare_maybe(self.denominator, other.denominator)

    def compare_raise(self, other: SyntaxNode) -> None:
        super().compare_raise(other)
        other = cast(TimesigFraction, other)

        self.numerator.compare_raise(other.numerator)
        self._compare_maybe(self.denominator, other.denominator, True)

    def value(self) -> Fraction:
        if self.denominator is None:
            return Fraction(self.numerator.value(), 1)
        return Fraction(self.numerator.value(), self.denominator.value())


class Numerator(SyntaxNode):
    """Represents a compound time signature numerator."""

    def __init__(self, digits_or_sum: List[Union[Number, Token]]) -> None:
        super().__init__()
        self.digits_or_sum = digits_or_sum

    def __str__(self) -> str:
        """Quick representation of the numerator for debugging."""
        return "".join(map(str, self.digits_or_sum))

    def __repr__(self) -> str:
        """Quick representation of the token for debugging."""
        return str(self)

    def accept(self, visitor: Visitor) -> Any:
        """Have visitor perform operation on node."""
        return visitor.visit_numerator(self)

    def compare(self, other: SyntaxNode) -> bool:
        if not isinstance(other, Numerator):
            return False
        return self._compare_lists(self.digits_or_sum, other.digits_or_sum)

    def compare_raise(self, other: SyntaxNode) -> None:
        super().compare_raise(other)
        other = cast(Numerator, other)
        self._compare_lists(self.digits_or_sum, other.digits_or_sum, True)

    def value(self) -> int:
        value = 0
        for obj in self.digits_or_sum:
            if isinstance(obj, Number):
                value += obj.value()
        return value


class Denominator(SyntaxNode):
    """Represents a compound time signature denominator."""

    def __init__(self, digits: Number) -> None:
        super().__init__()
        self.digits = digits

    def __str__(self) -> str:
        """Quick representation of the numerator for debugging."""
        return str(self.digits)

    def __repr__(self) -> str:
        """Quick representation of the token for debugging."""
        return str(self)

    def accept(self, visitor: Visitor) -> Any:
        """Have visitor perform operation on node."""
        return visitor.visit_denominator(self)

    def compare(self, other: SyntaxNode) -> bool:
        if not isinstance(other, Denominator):
            return False
        return self.digits.compare(other.digits)

    def compare_raise(self, other: SyntaxNode) -> None:
        super().compare_raise(other)
        other = cast(Denominator, other)

        self.digits.compare_raise(other.digits)

    def value(self) -> int:
        return self.digits.value()


class Number(SyntaxNode):
    """Represents a number in the notation."""

    def __init__(self, digits: List[Token]) -> None:
        super().__init__()
        self.digits = digits

    def __str__(self) -> str:
        """Quick representation of the numerator for debugging."""
        return "".join(map(str, self.digits))

    def __repr__(self) -> str:
        """Quick representation of the token for debugging."""
        return str(self)

    def accept(self, visitor: Visitor) -> Any:
        """Have visitor perform operation on node."""
        return visitor.visit_number(self)

    def compare(self, other: SyntaxNode) -> bool:
        if not isinstance(other, Number):
            return False
        return self._compare_lists(self.digits, other.digits)

    def compare_raise(self, other: SyntaxNode) -> None:
        super().compare_raise(other)
        other = cast(Number, other)

        self._compare_lists(self.digits, other.digits, True)

    def value(self) -> int:
        """Get the underlying value of the number."""
        return sum(
            x.modifiers["type"].value * (10**ii)
            for ii, x in enumerate(reversed(self.digits))
        )


class Clef(SyntaxNode):
    """Represents a clef symbol within the score."""

    def __init__(
        self,
        clef_token: Optional[Token],
        sign: TT.NamedPitch,
        octave: int,
        position: MS.StaffPosition,
    ) -> None:
        super().__init__()
        self.clef_token = clef_token
        self.sign = sign
        self.octave = octave
        self.position = position

    def __str__(self) -> str:
        """Quick representation of a clef for debugging."""
        return f"Clef: {str(self.clef_token)}"

    def __repr__(self) -> str:
        """Quick representation of the token for debugging."""
        return str(self)

    def accept(self, visitor: Visitor) -> Any:
        """Have visitor perform operation on node."""
        return visitor.visit_clef(self)

    def compare(self, other: SyntaxNode) -> bool:
        if not isinstance(other, Clef):
            return False

        return (
            self._compare_maybe(self.clef_token, other.clef_token)
            and self.sign == other.sign
            and self.octave == other.octave
            and self.position == other.position
        )

    def compare_raise(self, other: SyntaxNode) -> None:
        super().compare_raise(other)
        other = cast(Clef, other)

        self._compare_maybe(self.clef_token, other.clef_token, True)
        if not self.sign == other.sign:
            raise ValueError(
                f"Clef has the wrong sign: "
                f"Expected {self.sign} but got {other.sign}"
            )
        if not self.octave == other.octave:
            raise ValueError(
                f"Clef has the wrong octave. "
                f"Expected {self.octave} but got {other.octave}"
            )
        if not self.position == other.position:
            raise ValueError(
                f"Clef has the wrong position. "
                f"Expected {self.position} but got {other.position}"
            )

    def pitch2pos(self, pitch: MS.NotePitch) -> int:
        """Convert a full named pitch into a single staff-level position integer.

        Parameters
        ----------
        pitch : MS.NotePitch
            A notated pitch to convert using a specific clef.

        Returns
        -------
        int
            The resulting position on the staff counting from the first ledger line
            below the staff.
        """
        assert self.position.position is not None, "Uninitialised clef position"
        offset = (
            (self.octave * len(TT.NamedPitch))
            + self.sign.value
            - self.position.position
        )
        degree = pitch.step.value
        octave = pitch.octave

        return (octave * len(TT.NamedPitch) + degree) - offset

    def pos2pitch(self, pos: int) -> TT.NamedPitch:
        """Convert the position integer within a staff into a full musical pitch."""
        raise NotImplementedError

    @classmethod
    def from_token(cls, clef_token: Token) -> Clef:
        """Obtain all clef information from a token.

        Parameters
        ----------
        clef_token : Token
            The token from which to distill the info.

        Returns
        -------
        Clef
            A fully populated clef object.

        Raises
        ------
        ValueError
            If the token for the clef is not proper.
        """
        clef_type = clef_token.modifiers["type"]
        sign = MS.CLEF2SIGN[clef_type]
        octave_mod = int(clef_token.modifiers.get("oct", 0))
        octave = MS.DEFAULT_CLEF_OCTAVE[sign] + octave_mod

        return Clef(clef_type, sign, octave, clef_token.position)

    @classmethod
    def default_clef(cls, staff: int = 1) -> Clef:
        return Clef(
            None,
            TT.NamedPitch.G,
            MS.DEFAULT_CLEF_OCTAVE[TT.NamedPitch.G],
            MS.StaffPosition(staff, 4),
        )


class Key(SyntaxNode):
    """Represents a key signature change within the score."""

    RE_ACCIDENTAL = re.compile(r"accidental_(.*)")

    def __init__(
        self,
        accidentals: List[Token],
        naturals: List[Token],
        alterations: List[Optional[TT.AccidentalType]],
        fifths: Optional[int] = None,
    ) -> None:
        """Store alterations for a measure.

        Parameters
        ----------
        accidentals : List[Token]
            A list of accidentals to be drawn in the key.
        naturals: List[Token],
            A list of naturals that may cancel the previous key.
        alterations: List[MS.AccidentalType]
            A list of alterations per each canonical pitch.
        fifths: Optional[int] = None
            If the key is a standard fifth-circle one, the number of fifths to obtain
            it, None by default.
        """
        super().__init__()
        assert len(alterations) == len(TT.NamedPitch)
        self.naturals = naturals
        self.accidentals = accidentals
        self.alterations = alterations
        self.fifths = fifths

        self.sort()

    def __str__(self) -> str:
        """Quick representation of a key for debugging."""
        short_alters = [
            MS.ACCIDENTAL_SUMMARISED[x] if x is not None else " "
            for x in self.alterations
        ]
        return f"Key: {short_alters}"

    def __repr__(self) -> str:
        """Quick representation of the token for debugging."""
        return str(self)

    def accept(self, visitor: Visitor) -> Any:
        """Have visitor perform operation on node."""
        return visitor.visit_key(self)

    def compare(self, other: SyntaxNode) -> bool:
        if not isinstance(other, Key):
            return False

        # TODO: Key semantics are currently lost on re-loading MTN files, so this should
        # be disabled now to avoid false positives during tests.
        # if self.alterations != other.alterations:
        #     return False

        # if self.fifths != other.fifths:
        #     return False

        return self._compare_lists(
            self.naturals, other.naturals
        ) and self._compare_lists(self.accidentals, other.accidentals)

    def compare_raise(self, other: SyntaxNode) -> None:
        super().compare_raise(other)
        other = cast(Key, other)

        self._compare_lists(self.naturals, other.naturals, True)
        self._compare_lists(self.accidentals, other.accidentals, True)

    def sort(self):
        """Sort key accidentals according to MTN criteria."""
        self.naturals.sort(key=lambda x: int(x.position))
        self.accidentals.sort(key=lambda x: int(x.position))

    @classmethod
    def default_key(cls) -> Key:
        return Key([], [], [None for _ in range(len(TT.NamedPitch))], 0)

    # TODO: Factory methods from semantics to simplify conversion code
    @classmethod
    def from_fifths(cls, fifths: int, clef: Clef) -> Key: ...


class Direction(TopLevel):
    """Represents a direction within the score."""

    def __init__(
        self,
        delta: Fraction,
        directives: List[Token],
    ) -> None:
        super().__init__(delta)
        self.directives = directives

    def __str__(self) -> str:
        """Quick representation of a direction for debugging."""
        return f"Direction (Delta {self.delta}): {str(self.directives)}"

    def __repr__(self) -> str:
        """Quick representation of the token for debugging."""
        return str(self)

    def accept(self, visitor: Visitor) -> Any:
        """Have visitor perform operation on node."""
        return visitor.visit_direction(self)

    def compare(self, other: SyntaxNode) -> bool:
        if not isinstance(other, Direction):
            return False

        if self.delta != other.delta:
            return False

        return self._compare_lists(self.directives, other.directives)

    def compare_raise(self, other: SyntaxNode) -> None:
        super().compare_raise(other)
        other = cast(Direction, other)

        self._compare_lists(self.directives, other.directives, True)

    def merge(self, other: Direction) -> None:
        """Combine two direction objects that happen simultaneously."""
        assert (
            self.delta == other.delta
        ), "Attempting to merge directions at different time increments"

        self.directives += other.directives
        self.sort()

    def sort(self) -> None:
        """Sort internal elements according to MTN criteria."""
        self.directives.sort(
            key=lambda x: (
                x.token_type.value + f"_{x.modifiers['type'].value}"
                if "type" in x.modifiers
                else ""
            )
        )


class Measure(SyntaxNode):
    """Represents a measure within the score."""

    def __init__(
        self,
        elements: List[TopLevel],
        left_barline: Optional[Barline],
        right_barline: Optional[Barline],
        staves: int,
        measure_id: str,
        part_id: str,
        duration: Fraction,
    ) -> None:
        super().__init__()
        self.elements = elements

        self.left_barline = left_barline
        self.right_barline = right_barline

        self.staves = staves
        self.measure_id = measure_id
        self.part_id = part_id
        self.duration = duration

    def __str__(self) -> str:
        """Quick representation of a Measure for debugging."""
        return "\n".join(map(str, self.elements))

    def __repr__(self) -> str:
        """Quick representation of the token for debugging."""
        return str(self)

    def accept(self, visitor: Visitor) -> Any:
        """Have visitor perform operation on node."""
        return visitor.visit_measure(self)

    def compare(self, other: SyntaxNode) -> bool:
        if not isinstance(other, Measure):
            return False
        if not self.measure_id == other.measure_id:
            return False
        if not self.part_id == other.part_id:
            return False
        if not self.staves == other.staves:
            return False

        return (
            self._compare_lists(self.elements, other.elements)
            and self._compare_maybe(self.left_barline, other.left_barline)
            and self._compare_maybe(self.right_barline, other.right_barline)
        )

    def compare_raise(self, other: SyntaxNode) -> None:
        super().compare_raise(other)
        other = cast(Measure, other)

        self._compare_lists(self.elements, other.elements, True)
        self._compare_maybe(self.left_barline, other.left_barline, True)
        self._compare_maybe(self.right_barline, other.right_barline, True)

        if not self.measure_id == other.measure_id:
            raise ValueError(
                f"Wrong Measure ID. "
                f"Expected {self.measure_id} but got {other.measure_id}"
            )
        if not self.part_id == other.part_id:
            raise ValueError(
                f"Wrong Part ID. Expected {self.part_id} but got {other.part_id}"
            )
        if not self.staves == other.staves:
            raise ValueError(
                f"Wrong Number of Staves. "
                f"Expected {self.staves} but got {other.staves}"
            )

    def sort(self):
        """Sort internal elements according to MTN criteria."""
        self.elements.sort()


class Barline(TopLevel):
    """Represents a measure within the score."""

    def __init__(
        self,
        delta: Fraction,
        barline_tokens: List[Token],
        modifiers: List[Token],
    ) -> None:
        super().__init__(delta)
        self.barline_tokens = barline_tokens
        self.modifiers = modifiers

    def __str__(self) -> str:
        """Quick representation of a Barline for debugging."""
        return f"Barline (Delta {self.delta}): {str(self.barline_tokens)}"

    def __repr__(self) -> str:
        """Quick representation of the token for debugging."""
        return str(self)

    def accept(self, visitor: Visitor) -> Any:
        """Have visitor perform operation on node."""
        return visitor.visit_barline(self)

    def compare(self, other: SyntaxNode) -> bool:
        if not isinstance(other, Barline):
            return False
        if not self.delta == other.delta:
            return False

        return self._compare_lists(
            self.barline_tokens, other.barline_tokens
        ) and self._compare_lists(self.modifiers, other.modifiers)

    def compare_raise(self, other: SyntaxNode) -> None:
        super().compare_raise(other)
        other = cast(Barline, other)

        self._compare_lists(self.barline_tokens, other.barline_tokens, True)
        self._compare_lists(self.modifiers, other.modifiers, True)


class Score(SyntaxNode):
    """Represents a measure within the score."""

    def __init__(
        self,
        measures: List[Measure],
        score_id: str,
    ) -> None:
        super().__init__()
        self.measures = measures
        self.score_id = score_id

    def __str__(self) -> str:
        """Quick representation of a Score for debugging."""
        return "\n".join(map(str, self.measures))

    def __repr__(self) -> str:
        """Quick representation of the token for debugging."""
        return str(self)

    def accept(self, visitor: Visitor) -> Any:
        """Have visitor perform operation on node."""
        return visitor.visit_score(self)

    def compare(self, other: SyntaxNode) -> bool:
        if not isinstance(other, Score):
            return False

        # Not really useful
        # if not self.score_id == other.score_id:
        #     return False

        return self._compare_lists(self.measures, other.measures)

    def compare_raise(self, other: SyntaxNode) -> None:
        super().compare_raise(other)
        other = cast(Score, other)

        self._compare_lists(self.measures, other.measures, True)


_OBJECT_PRECEDENCE: Dict[Type[TopLevel], int] = {
    Barline: 1,
    Attributes: 2,
    Direction: 3,
    Rest: 4,
    NoteGroup: 5,
}
