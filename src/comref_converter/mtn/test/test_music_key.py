"""Test key object semantics and conversions."""

import unittest

from .. import semantics as MS
from .. import types as TT
from ..ast import Clef


class TestMusicalKey(unittest.TestCase):
    """Test MusicalKey operations."""

    def test_fifths_accidental_positions_gclef(self) -> None:
        """Test positions of accidentals on a G Clef."""
        clef = Clef(None, TT.NamedPitch.G, 4, position=MS.StaffPosition(1, 4))

        test_cases = [
            # fifths, result
            (7, [10, 7, 11, 8, 5, 9, 6]),
            (-7, [6, 9, 5, 8, 4, 7, 3]),
        ]
        for ii, (fifths, gt) in enumerate(test_cases):
            with self.subTest(i=ii):
                positions = MS.MusicalKey.fifths_accidental_positions(fifths, clef)
                self.assertEqual(positions, gt, f"Subtest {ii} failed")

    def test_fifths_accidental_positions_fclef(self) -> None:
        """Test positions of accidentals on an F Clef."""
        clef = Clef(None, TT.NamedPitch.F, 3, position=MS.StaffPosition(1, 8))

        test_cases = [
            # fifths, result
            (7, [8, 5, 9, 6, 3, 7, 4]),
            (-7, [4, 7, 3, 6, 2, 5, 1]),
        ]
        for ii, (fifths, gt) in enumerate(test_cases):
            with self.subTest(i=ii):
                positions = MS.MusicalKey.fifths_accidental_positions(fifths, clef)
                self.assertEqual(positions, gt, f"Subtest {ii} failed")
