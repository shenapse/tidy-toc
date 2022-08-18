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


def test_interpret_phrase_all(all_ok):
    for m in range(1, 100 + 1):
        for a in all_ok:
            inp = Interpreter(range_size=m)
            w = Interpreter.Word(a.data)
            assert inp._interpret_phrase(w) == inp.range


def test_interpret_phrase_none(none_ok):
    for m in range(1, 100 + 1):
        for a in none_ok:
            inp = Interpreter(range_size=m)
            w = Interpreter.Word(a.data)
            assert inp._interpret_phrase(w) == set()


def test_interpret_phrase_ng(integer_data, help_ok, ng):
    for a in integer_data + help_ok + ng:
        w = Interpreter.Word(a.data)
        inp = Interpreter(range_size=10)
        with pytest.raises(Exception):
            inp._interpret_phrase(w)


def test_interpret_digit_wrt_empty_set(digit_ok):
    M: int = max([int(d.data) for d in digit_ok])
    inp = Interpreter(range_size=M)
    for d in digit_ok:
        w = Interpreter.Word(d.data)
        digit = int(d.data)
        set_added = inp._interpret_digit_pattern(word=w)
        assert set_added == {digit}
        # add again should cause no change
        assert inp._interpret_digit_pattern(word=w, wrt=set_added) == {digit}


def test_interpret_minus_wrt_range(minus_ok):
    M: int = max(itertools.chain.from_iterable([d.res for d in minus_ok]))
    for d in minus_ok:
        d_int: int = d.res[0]
        w = Interpreter.Word(d.data)
        inp = Interpreter(range_size=M)
        # interpret minus pattern to range
        set_removed: set[int] = inp._interpret_minus_pattern(word=w, wrt=inp.range)
        # now the element is removed
        assert d_int not in set_removed
        # remove again should have no effect
        assert inp._interpret_minus_pattern(word=w, wrt=set_removed) == set_removed


def test_interpret_range_wrt_empty_set(range_ok):
    M: int = max(itertools.chain.from_iterable([d.res for d in range_ok]))
    for m in range(M, M + 100):
        for d in range_ok:
            d1, d2 = d.res[0], d.res[1]
            d_min: int = min(d1, d2)
            d_max: int = max(d1, d2)
            w = Interpreter.Word(d.data)
            inp = Interpreter(range_size=M)
            # coincides with [dmin,dmax]
            assert set(range(d_min, d_max + 1)) == inp._interpret_range_pattern(word=w)
