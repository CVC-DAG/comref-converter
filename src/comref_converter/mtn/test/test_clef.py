"""Test clef object semantics and conversions."""

import unittest
from fractions import Fraction

from .. import semantics as MS
from .. import types as TT
from ..ast import Clef


class TestClef(unittest.TestCase):
    """Test clef-related conversions."""

    def test_pitch2pos_gclef(self) -> None:
        """Test conversion from G-Clef to staff position."""
        clef = Clef(None, TT.NamedPitch.G, 4, position=MS.StaffPosition(1, 4))

        test_cases = [
            # Sign, Octave, Result
            (TT.NamedPitch.C, 4, 0),
            (TT.NamedPitch.G, 4, 4),
            (TT.NamedPitch.B, 3, -1),
            (TT.NamedPitch.C, 5, 7),
        ]
        for ii, (sign, octave, pos) in enumerate(test_cases):
            with self.subTest(i=ii):
                pitch = MS.NotePitch(sign, octave, Fraction(0))
                self.assertEqual(clef.pitch2pos(pitch), pos, f"Subtest {ii} failed")

    def test_pitch2pos_fclef(self) -> None:
        """Test conversion from F-Clef to staff position."""
        clef = Clef(None, TT.NamedPitch.F, 3, position=MS.StaffPosition(1, 8))

        test_cases = [
            # Sign, Octave, Result
            (TT.NamedPitch.C, 3, 5),
            (TT.NamedPitch.G, 3, 9),
            (TT.NamedPitch.B, 2, 4),
            (TT.NamedPitch.C, 4, 12),
        ]
        for ii, (sign, octave, pos) in enumerate(test_cases):
            with self.subTest(i=ii):
                pitch = MS.NotePitch(sign, octave, Fraction(0))
                self.assertEqual(clef.pitch2pos(pitch), pos, f"Subtest {ii} failed")

    def test_pitch2pos_cclef1(self) -> None:
        """Test conversion from C-Clef on line 1 to staff position."""
        clef = Clef(None, TT.NamedPitch.C, 4, position=MS.StaffPosition(1, 2))

        test_cases = [
            # Sign, Octave, Result
            (TT.NamedPitch.C, 4, 2),
            (TT.NamedPitch.G, 4, 6),
            (TT.NamedPitch.B, 3, 1),
            (TT.NamedPitch.C, 5, 9),
        ]
        for ii, (sign, octave, pos) in enumerate(test_cases):
            with self.subTest(i=ii):
                pitch = MS.NotePitch(sign, octave, Fraction(0))
                self.assertEqual(clef.pitch2pos(pitch), pos, f"Subtest {ii} failed")
