import os
import sys

sys.path.append(os.path.join(".", "scr"))


# from scr.Inputter import Inputter
from Inputter import Inputter  # type: ignore

#
# --------------------------------------
#   test start!
# --------------------------------------
#


def test_get_digit(digit_ok):
    inp = Inputter(max_line=100)
    for d in digit_ok:
        assert inp._get_matched_integers(Inputter.Digit, Inputter.Word(d.data)) == [int(d.data)]


def test_get_minus(minus_ok):
    inp = Inputter(max_line=100)
    for d in minus_ok:
        assert inp._get_matched_integers(Inputter.Minus, Inputter.Word(d.data)) == d.res


def test_get_range(range_ok):
    inp = Inputter(max_line=100)
    for d in range_ok:
        assert inp._get_matched_integers(Inputter.Range, Inputter.Word(d.data)) == d.res


def test_get_phrase_all(constants, all_ok):
    inp = Inputter(max_line=100)
    for d in all_ok:
        assert inp._get_matched_phrase(Inputter.Word(d.data)) == constants.name_all


def test_get_phrase_none(constants, none_ok):
    inp = Inputter(max_line=100)
    for d in none_ok:
        assert inp._get_matched_phrase(Inputter.Word(d.data)) == constants.name_none


def test_get_phrase_help(constants, help_ok):
    inp = Inputter(max_line=100)
    for d in help_ok:
        assert inp._get_matched_phrase(Inputter.Word(d.data)) == constants.name_help
