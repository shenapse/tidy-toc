import itertools
import os
import sys

import pytest

# from scr.Interpreter import Interpreter

sys.path.append(os.path.join(".", "scr"))


from Interpreter import Interpreter  # type: ignore

#
# --------------------------------------
#   test start!
# --------------------------------------
#


def add_space(texts: list[str]) -> list[str]:
    return list(itertools.chain.from_iterable([[text, f" {text}", f"{text} "] for text in texts]))


@pytest.fixture
def invalid_characters() -> list[str]:
    """characters not allowed by valid words"""
    inp = Interpreter(range_size=10)
    return [chr(i) for i in range(97, 123) if chr(i) not in inp.valid_words]


@pytest.fixture
def invalid_characters_mixed(invalid_characters) -> list[str]:
    inp = Interpreter(10)
    ok_words = inp.valid_words
    mixed: list[str] = []
    for w1 in ok_words:
        for w2 in ok_words:
            for v in invalid_characters:
                mixed.append(w1 + v + w2)
    return mixed


@pytest.fixture
def uninterpretable_sentence() -> list[str]:
    """combination of characters that is unable to interpret."""
    uninterpretable_valid_characters: list[str] = [" "] + add_space(
        [
            "l",
            "ll",
            "alll",
            "la",
            "lla",
            "nno",
            "ne",
        ]
    )
    uninterpretable_integers: list[str] = [
        "1-4 7-",
        "3 5--",
        "all -0 --1",
        "none 1 2 3 1--10",
        "a -8-9",
        "n 1-2-3",
        "1 -2-7-9",
        "8 2-4-2-",
    ]
    return uninterpretable_valid_characters + uninterpretable_integers


def get_range(start: int, end: int) -> list[int]:
    return list(range(start, end))


def interpret_sentence_ok_unit(max_line: int) -> list[tuple[str, list[int]]]:
    all: list[int] = get_range(0, max_line)
    digits = [
        ("1", [1]),
        ("0", [0]),
        ("20", [20]),
        ("1 2 3", [1, 2, 3]),
        ("10 8 3", [3, 8, 10]),
        ("5 19 3", [3, 5, 19]),
    ]
    range_d = [
        ("0-0", [0]),
        ("15-15", [15]),
        ("0-10", get_range(0, 10 + 1)),
        ("10-0", get_range(0, 10 + 1)),
        ("2-2 5-6", [2, 5, 6]),
        ("3-3 2-1", [1, 2, 3]),
        ("5-5 7-11", [5, 7, 8, 9, 10, 11]),
        ("0-1 5-2", [0, 1, 2, 3, 4, 5]),
    ]
    minus = [
        ("-5", []),
        ("-4 -3", []),
        ("0 -10", [0]),
        ("5 -5", []),
        ("1 -1", []),
        ("2 -1", [2]),
        ("-3 5 -5", []),
        ("-3 5 -3", [5]),
        ("-2 -5 -5", []),
        ("2 2 -2", []),
        ("-4 4 -4 4 ", [4]),
        ("4 -4 4 -4", []),
    ]
    phrase = [
        ("all", all),
        ("a", all),
        ("none", []),
        ("no", []),
        ("n", []),
        ("all none", []),
        ("no all", all),
        ("a n a", all),
        ("n a n", []),
    ]
    return digits + minus + range_d + phrase


def interpret_sentence_ok_mixed(max_line: int) -> list[tuple[str, list[int]]]:
    all = get_range(0, max_line)
    return [
        ("all none 1-4", get_range(1, 4 + 1)),
        ("all 1-5 none", []),
        ("all 5-6 -0", get_range(1, max_line)),
        ("-1 none all", all),
        ("2 -2 all", all),
        ("-4 all 6", all),
        ("6-7 none 6", [6]),
        ("none -4 none", []),
        ("all -2 2", all),
        ("1-3 4 -4", get_range(1, 3 + 1)),
        ("5 all 9-2", all),
        ("5 none -2", []),
        ("all 8 none", []),
        ("8-2 4 all", all),
        ("8-1 all none", []),
        ("none all -0", get_range(1, max_line)),
        ("-2 5 -5", []),
        ("1 1-10 none", []),
        ("none 4-0 all", all),
        ("-1 1 1-5", get_range(1, 5 + 1)),
        ("5-2 -2 9-1", get_range(1, 9 + 1)),
        ("all 7 all", all),
        ("none 6-1 7", get_range(1, 7 + 1)),
        ("none 9 1-2", [1, 2, 9]),
        ("8 1-2 9", [1, 2, 8, 9]),
    ]

    # term1   term2   term3
    # minus   range   none
    # all     none    range
    # all     range   minus
    # minus   none    all
    # digit   minus   all
    # minus   all     digit
    # range   none    digit
    # none    minus   none
    # all     minus   digit
    # range   digit   minus
    # digit   all     range
    # digit   none    minus
    # all     digit   none
    # range   digit   all
    # range   all     none
    # none    all     minus
    # minus   digit   minus
    # digit   range   none
    # none    range   all
    # minus   digit   range
    # range   minus   range
    # all     digit   all
    # none    range   digit
    # none    digit   range
    # digit   range   digit


#
# --------------------------------------
#   test start!
# --------------------------------------
#


def test_interpret_ng_on_invalid_characters(invalid_characters, invalid_characters_mixed):
    inp = Interpreter(range_size=20)
    for s in invalid_characters_mixed + invalid_characters:
        print(s)
        assert not inp.test_valid_characters(sentence=Interpreter.Sentence(s))


def test_interpret_ng_on_uninterpretable(uninterpretable_sentence):
    inp = Interpreter(range_size=20)
    for s in uninterpretable_sentence:
        # this uses valid characters but uninterpretable
        if not s == " ":  # space only character is forbidden by sentence class
            assert inp.test_valid_characters(sentence=Interpreter.Sentence(s))
        with pytest.raises(ValueError):
            inp._interpret(sentence=Interpreter.Sentence(s))


def test_interpret_ok_unit():
    for m in range(10, 100):
        inp = Interpreter(m)
        for data, ans in interpret_sentence_ok_unit(m):
            print(data)
            s = Interpreter.Sentence(data)
            assert sorted(inp._interpret(s)) == ans


def test_interpret_ok_mixed():
    for m in range(10, 100):
        inp = Interpreter(m)
        for data, ans in interpret_sentence_ok_mixed(m):
            s = Interpreter.Sentence(data)
            print(s)
            assert sorted(inp._interpret(s)) == ans
