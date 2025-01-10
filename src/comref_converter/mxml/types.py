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
MusicXML types.
"""


from enum import Enum


class AccidentalValue(Enum):
    """The accidental-value type represents notated accidentals supported by
    MusicXML.

    In the MusicXML 2.0 DTD this was a string with values that could be
    included. The XSD strengthens the data typing to an enumerated list.
    The quarter- and three-quarters- accidentals are Tartini-style
    quarter-tone accidentals. The -down and -up accidentals are quarter-
    tone accidentals that include arrows pointing down or up. The slash-
    accidentals are used in Turkish classical music. The numbered sharp
    and flat accidentals are superscripted versions of the accidental
    signs, used in Turkish folk music. The sori and koron accidentals
    are microtonal sharp and flat accidentals used in Iranian and
    Persian music. The other accidental covers accidentals other than
    those listed here. It is usually used in combination with the smufl
    attribute to specify a particular SMuFL accidental. The smufl
    attribute may be used with any accidental value to help specify the
    appearance of symbols that share the same MusicXML semantics.
    """

    SHARP = "sharp"
    NATURAL = "natural"
    FLAT = "flat"
    DOUBLE_SHARP = "double-sharp"
    SHARP_SHARP = "sharp-sharp"
    FLAT_FLAT = "flat-flat"
    NATURAL_SHARP = "natural-sharp"
    NATURAL_FLAT = "natural-flat"
    QUARTER_FLAT = "quarter-flat"
    QUARTER_SHARP = "quarter-sharp"
    THREE_QUARTERS_FLAT = "three-quarters-flat"
    THREE_QUARTERS_SHARP = "three-quarters-sharp"
    SHARP_DOWN = "sharp-down"
    SHARP_UP = "sharp-up"
    NATURAL_DOWN = "natural-down"
    NATURAL_UP = "natural-up"
    FLAT_DOWN = "flat-down"
    FLAT_UP = "flat-up"
    DOUBLE_SHARP_DOWN = "double-sharp-down"
    DOUBLE_SHARP_UP = "double-sharp-up"
    FLAT_FLAT_DOWN = "flat-flat-down"
    FLAT_FLAT_UP = "flat-flat-up"
    ARROW_DOWN = "arrow-down"
    ARROW_UP = "arrow-up"
    TRIPLE_SHARP = "triple-sharp"
    TRIPLE_FLAT = "triple-flat"
    SLASH_QUARTER_SHARP = "slash-quarter-sharp"
    SLASH_SHARP = "slash-sharp"
    SLASH_FLAT = "slash-flat"
    DOUBLE_SLASH_FLAT = "double-slash-flat"
    SHARP_1 = "sharp-1"
    SHARP_2 = "sharp-2"
    SHARP_3 = "sharp-3"
    SHARP_5 = "sharp-5"
    FLAT_1 = "flat-1"
    FLAT_2 = "flat-2"
    FLAT_3 = "flat-3"
    FLAT_4 = "flat-4"
    SORI = "sori"
    KORON = "koron"
    OTHER = "other"


class BackwardForward(Enum):
    """The backward-forward type is used to specify repeat directions.

    The start of the repeat has a forward direction while the end of the
    repeat has a backward direction.
    """

    BACKWARD = "backward"
    FORWARD = "forward"


class BarStyle(Enum):
    """The bar-style type represents barline style information.

    Choices are regular, dotted, dashed, heavy, light-light, light-
    heavy, heavy-light, heavy-heavy, tick (a short stroke through the
    top line), short (a partial barline between the 2nd and 4th lines),
    and none.
    """

    REGULAR = "regular"
    DOTTED = "dotted"
    DASHED = "dashed"
    HEAVY = "heavy"
    LIGHT_LIGHT = "light-light"
    LIGHT_HEAVY = "light-heavy"
    HEAVY_LIGHT = "heavy-light"
    HEAVY_HEAVY = "heavy-heavy"
    TICK = "tick"
    SHORT = "short"
    NONE = "none"


class BeamValue(Enum):
    """
    The beam-value type represents the type of beam associated with each of 8 beam
    levels (up to 1024th notes) available for each note.
    """

    BEGIN = "begin"
    CONTINUE = "continue"
    END = "end"
    FORWARD_HOOK = "forward hook"
    BACKWARD_HOOK = "backward hook"


class ClefSign(Enum):
    """The clef-sign type represents the different clef symbols.

    The jianpu sign indicates that the music that follows should be in
    jianpu numbered notation, just as the TAB sign indicates that the
    music that follows should be in tablature notation. Unlike TAB, a
    jianpu sign does not correspond to a visual clef notation. The none
    sign is deprecated as of MusicXML 4.0. Use the clef element's print-
    object attribute instead. When the none sign is used, notes should
    be displayed as if in treble clef.
    """

    G = "G"
    F = "F"
    C = "C"
    PERCUSSION = "percussion"
    TAB = "TAB"
    JIANPU = "jianpu"
    NONE = "none"


class FermataShape(Enum):
    """The fermata-shape type represents the shape of the fermata sign.

    The empty value is equivalent to the normal value.
    """

    NORMAL = "normal"
    ANGLED = "angled"
    SQUARE = "square"
    DOUBLE_ANGLED = "double-angled"
    DOUBLE_SQUARE = "double-square"
    DOUBLE_DOT = "double-dot"
    HALF_CURVE = "half-curve"
    CURLEW = "curlew"
    VALUE = ""


class LineType(Enum):
    """
    The line-type type distinguishes between solid, dashed, dotted, and wavy lines.
    """

    SOLID = "solid"
    DASHED = "dashed"
    DOTTED = "dotted"
    WAVY = "wavy"


class NoteSizeType(Enum):
    """The note-size-type type indicates the type of note being defined by a note-
    size element.

    The grace-cue type is used for notes of grace-cue size. The grace
    type is used for notes of cue size that include a grace element. The
    cue type is used for all other notes with cue size, whether defined
    explicitly or implicitly via a cue element. The large type is used
    for notes of large size.
    """

    CUE = "cue"
    GRACE = "grace"
    GRACE_CUE = "grace-cue"
    LARGE = "large"


class NoteTypeValue(Enum):
    """
    The note-type-value type is used for the MusicXML type element and represents
    the graphic note type, from 1024th (shortest) to maxima (longest).
    """

    VALUE_1024TH = "1024th"
    VALUE_512TH = "512th"
    VALUE_256TH = "256th"
    VALUE_128TH = "128th"
    VALUE_64TH = "64th"
    VALUE_32ND = "32nd"
    VALUE_16TH = "16th"
    EIGHTH = "eighth"
    QUARTER = "quarter"
    HALF = "half"
    WHOLE = "whole"
    BREVE = "breve"
    LONG = "long"
    MAXIMA = "maxima"


class NoteheadValue(Enum):
    """The notehead-value type indicates shapes other than the open and closed
    ovals associated with note durations.

    The values do, re, mi, fa, fa up, so, la, and ti correspond to
    Aikin's 7-shape system.  The fa up shape is typically used with
    upstems; the fa shape is typically used with downstems or no stems.
    The arrow shapes differ from triangle and inverted triangle by being
    centered on the stem. Slashed and back slashed notes include both
    the normal notehead and a slash. The triangle shape has the tip of
    the triangle pointing up; the inverted triangle shape has the tip of
    the triangle pointing down. The left triangle shape is a right
    triangle with the hypotenuse facing up and to the left. The other
    notehead covers noteheads other than those listed here. It is
    usually used in combination with the smufl attribute to specify a
    particular SMuFL notehead. The smufl attribute may be used with any
    notehead value to help specify the appearance of symbols that share
    the same MusicXML semantics. Noteheads in the SMuFL Note name
    noteheads and Note name noteheads supplement ranges (U+E150–U+E1AF
    and U+EEE0–U+EEFF) should not use the smufl attribute or the "other"
    value, but instead use the notehead-text element.
    """

    SLASH = "slash"
    TRIANGLE = "triangle"
    DIAMOND = "diamond"
    SQUARE = "square"
    CROSS = "cross"
    X = "x"
    CIRCLE_X = "circle-x"
    INVERTED_TRIANGLE = "inverted triangle"
    ARROW_DOWN = "arrow down"
    ARROW_UP = "arrow up"
    CIRCLED = "circled"
    SLASHED = "slashed"
    BACK_SLASHED = "back slashed"
    NORMAL = "normal"
    CLUSTER = "cluster"
    CIRCLE_DOT = "circle dot"
    LEFT_TRIANGLE = "left triangle"
    RECTANGLE = "rectangle"
    NONE = "none"
    DO = "do"
    RE = "re"
    MI = "mi"
    FA = "fa"
    FA_UP = "fa up"
    SO = "so"
    LA = "la"
    TI = "ti"
    OTHER = "other"


class PedalType(Enum):
    """The pedal-type simple type is used to distinguish types of pedal directions.

    The start value indicates the start of a damper pedal, while the
    sostenuto value indicates the start of a sostenuto pedal. The other
    values can be used with either the damper or sostenuto pedal. The
    soft pedal is not included here because there is no special symbol
    or graphic used for it beyond what can be specified with words and
    bracket elements. The change, continue, discontinue, and resume
    types are used when the line attribute is yes. The change type
    indicates a pedal lift and retake indicated with an inverted V
    marking. The continue type allows more precise formatting across
    system breaks and for more complex pedaling lines. The discontinue
    type indicates the end of a pedal line that does not include the
    explicit lift represented by the stop type. The resume type
    indicates the start of a pedal line that does not include the
    downstroke represented by the start type. It can be used when a line
    resumes after being discontinued, or to start a pedal line that is
    preceded by a text or symbol representation of the pedal.
    """

    START = "start"
    STOP = "stop"
    SOSTENUTO = "sostenuto"
    CHANGE = "change"
    CONTINUE = "continue"
    DISCONTINUE = "discontinue"
    RESUME = "resume"


class StartStopContinue(Enum):
    """The start-stop-continue type is used for an attribute of musical elements
    that can either start or stop, but also need to refer to an intermediate point
    in the symbol, as for complex slurs or for formatting of symbols across system
    breaks.

    The values of start, stop, and continue refer to how an element
    appears in musical score order, not in MusicXML document order. An
    element with a stop attribute may precede the corresponding element
    with a start attribute within a MusicXML document. This is
    particularly common in multi-staff music. For example, the stopping
    point for a slur may appear in staff 1 before the starting point for
    the slur appears in staff 2 later in the document. When multiple
    elements with the same tag are used within the same note, their
    order within the MusicXML document should match the musical score
    order. For example, a note that marks both the end of one slur and
    the start of a new slur should have the incoming slur element with a
    type of stop precede the outgoing slur element with a type of start.
    """

    START = "start"
    STOP = "stop"
    CONTINUE = "continue"


class StartStop(Enum):
    """The start-stop type is used for an attribute of musical elements that can
    either start or stop, such as tuplets.

    The values of start and stop refer to how an element appears in
    musical score order, not in MusicXML document order. An element with
    a stop attribute may precede the corresponding element with a start
    attribute within a MusicXML document. This is particularly common in
    multi-staff music. For example, the stopping point for a tuplet may
    appear in staff 1 before the starting point for the tuplet appears
    in staff 2 later in the document. When multiple elements with the
    same tag are used within the same note, their order within the
    MusicXML document should match the musical score order.
    """

    START = "start"
    STOP = "stop"


class StemValue(Enum):
    """
    The stem-value type represents the notated stem direction.
    """

    DOWN = "down"
    UP = "up"
    DOUBLE = "double"
    NONE = "none"


class Step(Enum):
    """
    The step type represents a step of the diatonic scale, represented using the
    English letters A through G.
    """

    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"


class TiedType(Enum):
    """The tied-type type is used as an attribute of the tied element to specify
    where the visual representation of a tie begins and ends.

    A tied element which joins two notes of the same pitch can be
    specified with tied-type start on the first note and tied-type stop
    on the second note. To indicate a note should be undamped, use a
    single tied element with tied-type let-ring. For other ties that are
    visually attached to a single note, such as a tie leading into or
    out of a repeated section or coda, use two tied elements on the same
    note, one start and one stop. In start-stop cases, ties can add more
    elements using a continue type. This is typically used to specify
    the formatting of cross-system ties. When multiple elements with the
    same tag are used within the same note, their order within the
    MusicXML document should match the musical score order. For example,
    a note with a tie at the end of a first ending should have the tied
    element with a type of start precede the tied element with a type of
    stop.
    """

    START = "start"
    STOP = "stop"
    CONTINUE = "continue"
    LET_RING = "let-ring"


class TimeRelation(Enum):
    """
    The time-relation type indicates the symbol used to represent the
    interchangeable aspect of dual time signatures.
    """

    PARENTHESES = "parentheses"
    BRACKET = "bracket"
    EQUALS = "equals"
    SLASH = "slash"
    SPACE = "space"
    HYPHEN = "hyphen"


class TimeSymbol(Enum):
    """The time-symbol type indicates how to display a time signature.

    The normal value is the usual fractional display, and is the implied
    symbol type if none is specified. Other options are the common and
    cut time symbols, as well as a single number with an implied
    denominator. The note symbol indicates that the beat-type should be
    represented with the corresponding downstem note rather than a
    number. The dotted-note symbol indicates that the beat-type should
    be represented with a dotted downstem note that corresponds to three
    times the beat-type value, and a numerator that is one third the
    beats value.
    """

    COMMON = "common"
    CUT = "cut"
    SINGLE_NUMBER = "single-number"
    NOTE = "note"
    DOTTED_NOTE = "dotted-note"
    NORMAL = "normal"


class UpDown(Enum):
    """
    The up-down type is used for the direction of arrows and other pointed symbols
    like vertical accents, indicating which way the tip is pointing.
    """

    UP = "up"
    DOWN = "down"


class UpDownStopContinue(Enum):
    """
    The up-down-stop-continue type is used for octave-shift elements, indicating
    the direction of the shift from their true pitched values because of printing
    difficulty.
    """

    UP = "up"
    DOWN = "down"
    STOP = "stop"
    CONTINUE = "continue"


class DynamicsType(Enum):
    """Dynamics can be associated either with a note or a general musical
    direction.

    To avoid inconsistencies between and amongst the letter
    abbreviations for dynamics (what is sf vs. sfz, standing alone or
    with a trailing dynamic that is not always piano), we use the actual
    letters as the names of these dynamic elements. The other-dynamics
    element allows other dynamic marks that are not covered here.
    Dynamics elements may also be combined to create marks not covered
    by a single element, such as sfmp. These letter dynamic symbols are
    separated from crescendo, decrescendo, and wedge indications.
    Dynamic representation is inconsistent in scores. Many things are
    assumed by the composer and left out, such as returns to original
    dynamics. The MusicXML format captures what is in the score, but
    does not try to be optimal for analysis or synthesis of dynamics.
    The placement attribute is used when the dynamics are associated
    with a note. It is ignored when the dynamics are associated with a
    direction. In that case the direction element's placement attribute
    is used instead.
    """

    P = "p"
    PP = "pp"
    PPP = "ppp"
    PPPP = "pppp"
    PPPPP = "ppppp"
    PPPPPP = "pppppp"
    F = "f"
    FF = "ff"
    FFF = "fff"
    FFFF = "ffff"
    FFFFF = "fffff"
    FFFFFF = "ffffff"
    MP = "mp"
    MF = "mf"
    SF = "sf"
    SFP = "sfp"
    SFPP = "sfpp"
    FP = "fp"
    RF = "rf"
    RFZ = "rfz"
    SFZ = "sfz"
    SFFZ = "sffz"
    FZ = "fz"
    N = "n"
    PF = "pf"
    SFZP = "sfzp"
    OTHER_DYNAMICS = "other-dynamics"


class WedgeType(Enum):
    """The wedge type is crescendo for the start of a wedge that is closed at the
    left side, diminuendo for the start of a wedge that is closed on the right
    side, and stop for the end of a wedge.

    The continue type is used for formatting wedges over a system break,
    or for other situations where a single wedge is divided into
    multiple segments.
    """

    CRESCENDO = "crescendo"
    DIMINUENDO = "diminuendo"
    STOP = "stop"
    CONTINUE = "continue"
