import os
import sys

sys.path.append(os.path.join(".", "scr"))
from typing import TypeAlias

import pytest
from Page_Corrector import Mediator

# from scr.Page_Corrector import Mediator


def get_alphabets() -> list[str]:
    return [chr(ord("a") + i) for i in range(26)]


@pytest.fixture
def data_test_digit() -> list[tuple[str, bool]]:
    return [
        ("23", True),
        ("+23", True),
        ("-23", True),
        ("0", True),
        ("+0", True),
        ("-0", True),
        ("a", False),
        ("1a", False),
        ("a1", False),
        ("", False),
    ]


@pytest.fixture
def data_convert_input_ok() -> list[tuple[str, str | int, Mediator.Integer_Flag]]:
    """assumes 's' options are allowed"""
    med = Mediator()
    n = med.Integer_Flag.Normal
    p = med.Integer_Flag.Plus
    return [("10", 10, n), ("-1", -1, n), ("+9", 9, p)] + [(option, option, n) for option in med._public_options]


@pytest.fixture
def data_range_out() -> list[tuple[str, bool]]:
    med = Mediator()
    thr: int = med._max_page
    return [
        (str(-thr - 1), False),
        (str(-thr), True),
        (str(thr), True),
        (str(thr + 1), False),
    ]


@pytest.fixture
def data_convert_input_ng() -> list[tuple[str, None, Mediator.Integer_Flag]]:
    """assumes some options are allowed"""
    med = Mediator()
    n = Mediator.Integer_Flag.Normal
    return [(c, None, n) for c in get_alphabets() if c not in med._public_options]


# -------------------------
#   test start!
# -------------------------


def test_test_digit(data_test_digit):
    P = Mediator()
    for inp, ans in data_test_digit:
        print(f"inp={inp}, ans={ans}")
        assert P._test_digit(inp) == ans


def test_convert_input_ok(data_convert_input_ok):
    P = Mediator()
    for inp, ans_out, ans_flag in data_convert_input_ok:
        out, flag = P._convert_input(inp)
        print(f"inp={inp}, acutal out={out}")
        assert out == ans_out
        assert flag == ans_flag


def test_range_out(data_range_out):
    P = Mediator()
    for inp, res in data_range_out:
        converted, _ = P._convert_input(inp)
        assert isinstance(converted, int) and P._test_range(converted) == res


def test_convert_input_ng(data_convert_input_ng):
    P = Mediator()
    for inp, ans_out, ans_flag in data_convert_input_ng:
        out, flag = P._convert_input(inp)
        assert out == ans_out
        assert flag == ans_flag
