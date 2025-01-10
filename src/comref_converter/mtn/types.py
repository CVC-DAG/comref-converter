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
MTN token definitions and object types.
"""

from __future__ import annotations

from enum import Enum, unique
from fractions import Fraction
from math import ceil, log
from typing import Optional


@unique
class TokenType(Enum):
    """Defines all possible token types."""

    # BOW = auto()
    # BRACKET = auto()
    # BREATH_MARK = auto()
    # DASHES = auto()
    # DOIT = auto()
    # ENDING = auto()
    # LEGATO = auto()
    # NON_ARPEGGIATE = auto()
    # OCTAVE_SHIFT = auto()
    # OPEN_STRING = auto()
    # SCOOP = auto()
    # STOPPED = auto()
    ACCENT = "accent"
    ACCIDENTAL = "accidental"
    ARPEGGIATE = "arpeggiate"
    BARLINE = "barline_tok"
    BEAM = "beam"
    CAESURA = "caesura"
    CLEF = "clef"
    CODA = "coda"
    DELTA = "delta"
    DOT = "dot"
    DYN = "dyn"
    EOF = "eof"
    FERMATA = "fermata"
    FLAG = "flag"
    GLISSANDO = "glissando"
    HAYDN = "haydn"
    MORDENT = "mordent"
    NOTEHEAD = "notehead"
    NUMBER = "number"
    OVER = "over"
    PEDAL = "pedal"
    PLUS = "plus"
    REPEAT = "repeat"
    REST = "rest"
    SCHLEIFER = "schleifer"
    SEGNO = "segno"
    SLIDE = "slide"
    SLUR = "slur"
    STACCATO = "staccato"
    STEM = "stem"
    TENUTO = "tenuto"
    TIED = "tied"
    TIME_RELATION = "time_relation"
    TIMESIG = "timesig"
    TRILL = "trill"
    TUPLET = "tuplet"
    TURN = "turn"
    UNKNOWN = "unknown"
    WAVY_LINE = "wavy_line"
    WEDGE = "wedge"


class AccidentalType(Enum):
    """Models accidental types."""

    ACC_SHARP = "sharp"
    ACC_NATURAL = "natural"
    ACC_FLAT = "flat"
    ACC_DOUBLE_SHARP = "double_sharp"
    ACC_DOUBLE_FLAT = "double_flat"
    ACC_QUARTER_FLAT = "quarter_flat"
    ACC_QUARTER_SHARP = "quarter_sharp"


class NoteType(Enum):
    """Models note types according to duration."""

    NT_MAXIMA = "maxima"
    NT_LONG = "long"
    NT_BREVE = "breve"
    NT_WHOLE = "whole"
    NT_HALF = "half"
    NT_QUARTER = "quarter"
    NT_EIGHTH = "eighth"
    NT_16TH = "16th"
    NT_32ND = "32nd"
    NT_64TH = "64th"
    NT_128TH = "128th"
    NT_256TH = "256th"
    NT_512TH = "512th"
    NT_1024TH = "1024th"

    @classmethod
    def type2duration(cls, ntype: NoteType) -> Fraction:
        """Return the duration of a specified note type."""
        return TYPE2DURATION[ntype]

    @classmethod
    def duration2type(cls, dur: Fraction) -> NoteType:
        """Return the note type class for a specified duration."""
        try:
            return DURATION2TYPE[dur]
        except KeyError:
            try:
                return DURATION2TYPE[cls._closest_pow2(dur)]
            except KeyError:
                return NoteType.NT_WHOLE

    @classmethod
    def beams2type(cls, nbeams: int) -> NoteType:
        """Get the note type based on the number of beams."""
        return BEAM2TYPE[nbeams]

    @classmethod
    def type2beams(cls, ntype: NoteType) -> Optional[int]:
        """Get the number of beams based on the note type."""
        return TYPE2BEAM.get(ntype, None)

    @classmethod
    def _closest_pow2(cls, dur: Fraction) -> Fraction:
        exponent = ceil(log(dur, 2))

        if exponent >= 0:
            return Fraction(2**exponent)
        return Fraction(1, 2**-exponent)


TYPE2DURATION = {
    NoteType.NT_MAXIMA: Fraction(8, 1),
    NoteType.NT_LONG: Fraction(4, 1),
    NoteType.NT_BREVE: Fraction(2, 1),
    NoteType.NT_WHOLE: Fraction(1, 1),
    NoteType.NT_HALF: Fraction(1, 2),
    NoteType.NT_QUARTER: Fraction(1, 4),
    NoteType.NT_EIGHTH: Fraction(1, 8),
    NoteType.NT_16TH: Fraction(1, 16),
    NoteType.NT_32ND: Fraction(1, 32),
    NoteType.NT_64TH: Fraction(1, 64),
    NoteType.NT_128TH: Fraction(1, 128),
    NoteType.NT_256TH: Fraction(1, 256),
    NoteType.NT_512TH: Fraction(1, 512),
    NoteType.NT_1024TH: Fraction(1, 1024),
}
DURATION2TYPE = {dur: typ for typ, dur in TYPE2DURATION.items()}

BEAM2TYPE = {x - 2: DURATION2TYPE[Fraction(1, 2**x)] for x in range(2, 11)}
TYPE2BEAM = {typ: num for num, typ in BEAM2TYPE.items()}


class NoteheadType(Enum):
    """Models the type of notehead in use."""

    NH_BLACK = "black"
    NH_WHITE = "white"
    NH_MAXIMA = "maxima"
    NH_LONG = "long"
    NH_BREVE = "breve"
    NH_CROSS = "cross"
    NH_TRIANGLE = "triangle"
    NH_INVERTED_TRIANGLE = "inverted-triangle"
    NH_DIAMOND = "diamond"

    # Less common types -- future support
    # NH_ARROW_DOWN = "arrow_down"
    # NH_ARROW_UP = "arrow_up"
    # NH_BACK_SLASHED = "back_slashed"
    # NH_CIRCLE_DOT = "circle_dot"
    # NH_CIRCLE_X = "circle_x"
    # NH_CIRCLED = "circled"
    # NH_CLUSTER = "cluster"

    @classmethod
    def type2notehead(cls, ntype: NoteType) -> NoteheadType:
        """Get the notehead type corresponding to this note type."""
        return TYPE2NOTEHEAD[ntype]


TYPE2NOTEHEAD = {
    NoteType.NT_MAXIMA: NoteheadType.NH_MAXIMA,
    NoteType.NT_LONG: NoteheadType.NH_LONG,
    NoteType.NT_BREVE: NoteheadType.NH_BREVE,
    NoteType.NT_WHOLE: NoteheadType.NH_WHITE,
    NoteType.NT_HALF: NoteheadType.NH_WHITE,
    NoteType.NT_QUARTER: NoteheadType.NH_BLACK,
    NoteType.NT_EIGHTH: NoteheadType.NH_BLACK,
    NoteType.NT_16TH: NoteheadType.NH_BLACK,
    NoteType.NT_32ND: NoteheadType.NH_BLACK,
    NoteType.NT_64TH: NoteheadType.NH_BLACK,
    NoteType.NT_128TH: NoteheadType.NH_BLACK,
    NoteType.NT_256TH: NoteheadType.NH_BLACK,
    NoteType.NT_512TH: NoteheadType.NH_BLACK,
    NoteType.NT_1024TH: NoteheadType.NH_BLACK,
}


class BarlineType(Enum):
    """Models the type of barline in use."""

    BL_REGULAR = "regular"
    BL_DOTTED = "dotted"
    BL_DASHED = "dashed"
    BL_HEAVY = "heavy"
    BL_TICK = "tick"
    BL_SHORT = "short"


class NamedPitch(Enum):
    """Models CWMN note pitches."""

    C = 0
    D = 1
    E = 2
    F = 3
    G = 4
    A = 5
    B = 6


class ClefType(Enum):
    """Models clef types."""

    CLEF_G = "G"
    CLEF_C = "C"
    CLEF_F = "F"
    CLEF_PERCUSSION = "percussion"


class StartStop(Enum):
    """Models starting or ending sides of an ongoing element."""

    START = "start"
    STOP = "stop"


class StemDirection(Enum):
    """Models the direction a stem is pointing."""

    UP = "up"
    DOWN = "down"


class Digits(Enum):
    """Models any digits that appear physically on the score."""

    DIGIT_0 = 0
    DIGIT_1 = 1
    DIGIT_2 = 2
    DIGIT_3 = 3
    DIGIT_4 = 4
    DIGIT_5 = 5
    DIGIT_6 = 6
    DIGIT_7 = 7
    DIGIT_8 = 8
    DIGIT_9 = 9


class DynamicsType(Enum):
    """Models any possible dynamic tokens."""

    DYN_P = "p"
    DYN_PP = "pp"
    DYN_PPP = "ppp"
    DYN_PPPP = "pppp"
    DYN_PPPPP = "ppppp"
    DYN_PPPPPP = "pppppp"
    DYN_F = "f"
    DYN_FF = "ff"
    DYN_FFF = "fff"
    DYN_FFFF = "ffff"
    DYN_FFFFF = "fffff"
    DYN_FFFFFF = "ffffff"
    DYN_MP = "mp"
    DYN_MF = "mf"
    DYN_SF = "sf"
    DYN_SFP = "sfp"
    DYN_SFPP = "sfpp"
    DYN_FP = "fp"
    DYN_RF = "rf"
    DYN_RFZ = "rfz"
    DYN_SFZ = "sfz"
    DYN_SFFZ = "sffz"
    DYN_FZ = "fz"
    DYN_N = "n"
    DYN_PF = "pf"
    DYN_SFZP = "sfzp"


class TimeSymbol(Enum):
    """Models a single object as a time signature."""

    TS_COMMON = "common"
    TS_CUT = "cut"


class TimeRelation(Enum):
    """Models a time relationship symbol,"""

    TR_EQUALS = "equals"


class WedgeType(Enum):
    """Model a wedge."""

    WEDGE_CRESCENDO = "crescendo"
    WEDGE_DIMINUENDO = "diminuendo"
    WEDGE_STOP = "stop"


class BackwardForward(Enum):
    """Represents something that can aim forwards or backwards."""

    DIR_BACKWARD = "backward"
    DIR_FORWARD = "forward"
