import os
import sys
from re import Pattern

import pytest

sys.path.append(os.path.join(".", "scr"))

from Interpreter import Interpreter  # type: ignore

# from scr.Interpreter import Interpreter


#
# --------------------------------------
#   test start!
# --------------------------------------


# test Phrase
def test_get_dominant_word(constants):
    for x in range(1, 101, 10):
        assert Interpreter(x).Phrase.get_dominant_names() == [constants.name_help]


def test_get_pattern_of_phrase(constants):
    for x in range(1, 101, 10):
        get_pat = Interpreter(range_size=x).Phrase.get_pattern
        assert get_pat(constants.name_none) == constants.pat_none
        assert get_pat(constants.name_all) == constants.pat_all
        assert get_pat(constants.name_help) == constants.pat_help


def test_test_match_digit_ok(constants, digit_ok):
    inp = Interpreter(range_size=10)
    ok_sample: list[str] = [d.data for d in digit_ok]
    for s in ok_sample:
        assert inp._test_match(constants.pat_digit, Interpreter.Word(s))


def test_test_match_digit_ng(constants, minus_ok, range_ok, ng):
    inp = Interpreter(range_size=10)
    ng_sample: list[str] = [d.data for d in (minus_ok + range_ok + ng)]
    for s in ng_sample:
        assert not inp._test_match(constants.pat_digit, Interpreter.Word(s))


def test_test_match_minus_ok(constants, minus_ok):
    inp = Interpreter(range_size=10)
    ok_sample: list[str] = [d.data for d in minus_ok]
    for s in ok_sample:
        assert inp._test_match(constants.pat_minus, Interpreter.Word(s))


def test_test_match_minus_ng(constants, digit_ok, range_ok, ng):
    inp = Interpreter(range_size=10)
    ng_sample: list[str] = [d.data for d in (digit_ok + range_ok + ng)]
    for s in ng_sample:
        assert not inp._test_match(constants.pat_minus, Interpreter.Word(s))


def test_test_match_range_ok(constants, range_ok):
    inp = Interpreter(range_size=10)
    ok_sample: list[str] = [d.data for d in range_ok]
    for s in ok_sample:
        assert inp._test_match(constants.pat_range, Interpreter.Word(s))


def test_test_match_range_ng(constants, digit_ok, minus_ok, ng):
    inp = Interpreter(range_size=10)
    ng_sample: list[str] = [d.data for d in (digit_ok + minus_ok + ng)]
    for s in ng_sample:
        assert not inp._test_match(constants.pat_range, Interpreter.Word(s))


def test_test_match_any_ok(constants, phrase_data, integer_data):
    inp = Interpreter(range_size=10)
    pat_any: list[Pattern] = [
        constants.pat_none,
        constants.pat_all,
        constants.pat_help,
        constants.pat_digit,
        constants.pat_minus,
        constants.pat_range,
    ]
    ok_sample: list[str] = [d.data for d in (phrase_data + integer_data)]
    for word in ok_sample:
        assert inp._test_match_by(pats=pat_any, word=Interpreter.Word(word))


def test_match_any_ng(constants, ng):
    inp = Interpreter(range_size=10)
    pat_any: list[Pattern] = [
        constants.pat_none,
        constants.pat_all,
        constants.pat_help,
        constants.pat_digit,
        constants.pat_minus,
        constants.pat_range,
    ]
    ng_sample: list[str] = [d.data for d in ng]
    for word in ng_sample:
        assert not inp._test_match_by(pats=pat_any, word=Interpreter.Word(word))


def test_test_match_none_ok(constants, none_ok):
    inp = Interpreter(range_size=10)
    ok_sample: list[str] = [d.data for d in none_ok]
    for s in ok_sample:
        assert inp._test_match(constants.pat_none, Interpreter.Word(s))


def test_test_match_none_ng(constants, integer_data, all_ok, help_ok, ng):
    inp = Interpreter(range_size=10)
    ng_sample: list[str] = [d.data for d in (integer_data + all_ok + help_ok + ng)]
    for s in ng_sample:
        assert not inp._test_match(constants.pat_none, Interpreter.Word(s))


def test_test_match_help_ok(constants, help_ok):
    inp = Interpreter(range_size=10)
    ok_sample: list[str] = [d.data for d in help_ok]
    for s in ok_sample:
        assert inp._test_match(constants.pat_help, Interpreter.Word(s))


def test_test_match_help_ng(constants, integer_data, all_ok, none_ok, ng):
    inp = Interpreter(range_size=10)
    ng_sample: list[str] = [d.data for d in (integer_data + all_ok + none_ok + ng)]
    for s in ng_sample:
        assert not inp._test_match(constants.pat_help, Interpreter.Word(s))


def test_exsist_dominant_phrase_ok(help_ok):
    inp = Interpreter(range_size=10)
    ok_sample: list[str] = [d.data for d in help_ok]
    for s in ok_sample:
        assert inp._exist_dominant_phrase(Interpreter.Sentence(s))
