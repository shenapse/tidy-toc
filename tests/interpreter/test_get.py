import os
import sys

sys.path.append(os.path.join(".", "scr"))


# from scr.Interpreter import Interpreter
from Interpreter import Interpreter  # type: ignore

#
# --------------------------------------
#   test start!
# --------------------------------------
#


def test_get_digit(digit_ok):
    inp = Interpreter(range_size=100)
    for d in digit_ok:
        assert inp._get_matched_integers(Interpreter.Digit, Interpreter.Word(d.data)) == [int(d.data)]


def test_get_minus(minus_ok):
    inp = Interpreter(range_size=100)
    for d in minus_ok:
        assert inp._get_matched_integers(Interpreter.Minus, Interpreter.Word(d.data)) == d.res


def test_get_range(range_ok):
    inp = Interpreter(range_size=100)
    for d in range_ok:
        assert inp._get_matched_integers(Interpreter.Range, Interpreter.Word(d.data)) == d.res


def test_get_phrase_all(constants, all_ok):
    inp = Interpreter(range_size=100)
    for d in all_ok:
        assert inp._get_matched_phrase(Interpreter.Word(d.data)) == constants.name_all


def test_get_phrase_none(constants, none_ok):
    inp = Interpreter(range_size=100)
    for d in none_ok:
        assert inp._get_matched_phrase(Interpreter.Word(d.data)) == constants.name_none


def test_get_phrase_help(constants, help_ok):
    inp = Interpreter(range_size=100)
    for d in help_ok:
        assert inp._get_matched_phrase(Interpreter.Word(d.data)) == constants.name_help
