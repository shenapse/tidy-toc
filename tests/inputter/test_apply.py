import itertools
import os
import sys

import pytest

# from scr.Inputter import Inputter

sys.path.append(os.path.join(".", "scr"))


from Inputter import Inputter  # type: ignore

#
# --------------------------------------
#   test start!
# --------------------------------------
#


def test_apply_phrase_all_when_input_is_empty(all_ok):
    for m in range(1, 100 + 1):
        for a in all_ok:
            inp = Inputter(max_line=m)
            inp._apply_phrase(a.data)
            assert inp.input == inp.range


def test_apply_phrase_none_when_input_is_full(none_ok):
    for m in range(1, 100 + 1):
        for a in none_ok:
            inp = Inputter(max_line=m)
            # set it full
            inp._apply_phrase("all")
            # then clear
            inp._apply_phrase(a.data)
            # now it must be empty
            assert inp.input == set()


def test_apply_phrase_ng(integer_data, help_ok, ng):
    for a in integer_data + help_ok + ng:
        inp = Inputter(max_line=10)
        with pytest.raises(Exception):
            inp._apply_phrase(a)


def test_apply_digit_when_input_is_empty(digit_ok):
    M: int = max([int(d.data) for d in digit_ok])
    inp = Inputter(max_line=M)
    for d in digit_ok:
        # clear input
        inp.clear()
        inp._apply_digit_pattern(d.data)
        assert inp.input == {int(d.data)}
        # add again should cause no change
        inp._apply_digit_pattern(d.data)
        assert inp.input == {int(d.data)}


def test_apply_minus_when_input_is_full(minus_ok):
    M: int = max(itertools.chain.from_iterable([d.res for d in minus_ok]))
    for d in minus_ok:
        d_int: int = d.res[0]
        inp = Inputter(max_line=M)
        print(inp.range)
        # make it full
        inp._apply_phrase("all")
        # current input should contain input integer since it is full
        assert d_int in inp.input
        # apply minus pattern
        inp._apply_minus_pattern(d.data)
        # now the element is removed
        assert d_int not in inp.input
        input_before: set[int] = inp.input
        # remove again should have no effect
        inp._apply_minus_pattern(d.data)
        assert inp.input == input_before


def test_apply_range_when_input_is_empty(range_ok):
    M: int = max(itertools.chain.from_iterable([d.res for d in range_ok]))
    for m in range(M, M + 100):
        for d in range_ok:
            d1, d2 = d.res[0], d.res[1]
            d_min: int = min(d1, d2)
            d_max: int = max(d1, d2)
            inp = Inputter(max_line=M)
            # input starts with empty
            assert inp.input == set()
            inp._apply_range_pattern(d.data)
            # now inp.input has all the element [dmin,dmax]
            assert set(range(d_min, d_max + 1)) == inp.input
