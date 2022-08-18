import os
import sys

import pytest

sys.path.append(os.path.join(".", "scr"))
from Merger import Merger
from Text_Line import Paged_Text_Line
from Text_Lines import Paged_Text_Lines

# from scr.Merger import Merger
# from scr.Text_Line import Paged_Text_Line, Paged_Text_Lines, Text_Line, Text_Lines


def to_ptls(idx: list[int], texts: list[str]) -> Paged_Text_Lines:
    assert len(idx) == len(texts)
    idx.sort()
    return Paged_Text_Lines([Paged_Text_Line(idx[i], s) for i, s in enumerate(texts)])


@pytest.fixture
def data_merge_cand_ok() -> list[tuple[list[int], list[str], list[int]]]:
    """input text + idx of expected cand"""
    data_and_res = [
        ([0, 1], ["1.1 hello", "5"], [0]),
        ([1, 2], ["1.1 hello", "world 15"], [1]),
        ([3, 4], ["1.1 hello", "world"], [3]),
        ([5, 6], ["A. hello", "world 14"], [5]),
        ([7, 8], ["A. hello", "world"], [7]),
        ([9, 10], ["Chapter 1. hello", "world 15"], [9]),
        ([1, 4], ["Chapter 1. hello", "world"], [1]),
    ]
    return data_and_res


@pytest.fixture
def data_merge_cand_ng() -> list[tuple[list[int], list[str], list[int]]]:
    """input text + idx of expected cand"""
    data_and_res = [
        ([1, 2], ["hello 1", "world 15"], []),
        ([3, 4], ["hello iv", "world 15"], []),
        ([5, 6], ["1.1 hello", "1.2 world 6"], []),
        ([5, 6], ["1.1 hello 5", "1.2 world 6"], []),
        ([7, 8], ["A. hello", "B. world 14"], []),
        ([9, 10], ["A. hello", "1.2. world 14"], []),
        ([1, 2], ["Chapter 1. hello", "3.1 world 15"], []),
        ([5, 6], ["jlasjf hello", "world 14"], []),
    ]
    return data_and_res


@pytest.fixture
def data_merge() -> list[tuple[list[str], str, int]]:
    """input text + idx of expected cand"""
    data_and_res = [
        ([1, 2], ["without page", "page 15"], "without page page", 15),
        ([1, 2], ["without page A.", "page58"], "without page A. page", 58),
    ]
    return data_and_res


def test_merge_cand_ok(data_merge_cand_ok):
    for idx, s, ans in data_merge_cand_ok:
        ptls = to_ptls(idx, s)
        mer = Merger(ptls)
        print(ptls)
        mer_cand = mer.get_candidates2()
        assert mer_cand.get_index() == ans


def test_merge_cand_ng(data_merge_cand_ng):
    for idx, s, ans in data_merge_cand_ng:
        ptls = to_ptls(idx, s)
        mer = Merger(ptls)
        print(ptls)
        mer_cand = mer.get_candidates2()
        assert mer_cand.get_index() == ans


def test_merge(data_merge):
    for idx, s, text, page in data_merge:
        ptls = to_ptls(idx, s)
        mer = Merger(ptls)
        merged = mer._merge(ptls[0], ptls[1])
        print(merged)
        assert merged.text == text
        assert merged.page_number == page
