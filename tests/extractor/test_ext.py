import os
import sys

import pytest

# from scr.Extractor import Extractor
# from scr.Text_Line import Paged_Text_Line
# from scr.Text_Lines import Paged_Text_Lines, _Text_Lines

sys.path.append(os.path.join(".", "scr"))
from Extractor2 import Extractor
from Text_Line import Paged_Text_Line
from Text_Lines import Paged_Text_Lines


def to_ptls(idx: list[int], texts: list[str]) -> Paged_Text_Lines:
    assert len(idx) == len(texts)
    idx.sort()
    return Paged_Text_Lines([Paged_Text_Line(idx[i], s) for i, s in enumerate(texts)])


@pytest.fixture
def data_unexpected_roman_page() -> list[tuple[list[str], list[int]]]:
    """sample strings for paged text line and list of row indexes that should be extracted"""
    # term1	term2	term3
    # main	main	main
    # main	none	front
    # none	main	none
    # front	main	front
    # none	front	main
    # front	front	none
    # main	front	front
    # front	none	main
    # main	none	none
    # none	none	front
    m: str = "main 5"
    f: str = "front ix"
    n: str = "with no page"
    return [
        ([m, m, m], []),
        ([m, n, f], [2]),
        ([n, m, n], []),
        ([f, m, f], [2]),
        ([n, f, m], []),
        ([f, f, n], []),
        ([m, f, f], [1, 2]),
        ([f, n, m], []),
        ([m, n, n], []),
        ([n, n, f], []),
    ]


@pytest.fixture
def data_starts_with_roman_page() -> list[tuple[list[str], list[int]]]:
    """sample strings for paged text line and list of row indexes that should be extracted"""
    r: str = "xx roman"
    a: str = "1.1.1 dummy 5"
    n: str = "with no page"
    return [([r], [0]), ([a], []), ([n], [])]


def test_get_lines_with_unexpected_roman_page(data_unexpected_roman_page):
    for text, idx in data_unexpected_roman_page:
        e = Extractor(text)
        res = e.get_lines_with_unexpected_roman_page()
        assert res.get_index() == idx


def test_get_lines_start_with_roman_number(data_starts_with_roman_page):
    for text, idx in data_starts_with_roman_page:
        e = Extractor(text)
        res = e._get_lines_start_with_roman_number()
        assert res.get_index() == idx
