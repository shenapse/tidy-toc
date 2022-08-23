import os
import re
import sys
from re import Match, Pattern

import pytest

sys.path.append(os.path.join(".", "scr"))
from Text_Line import Paged_Text_Line, Text_Line  # type: ignore

# from scr.Text_Line import Paged_Text_Line

H = Paged_Text_Line.Header


@pytest.fixture
def text_with_arabic_page() -> list[tuple[str, str, int | None]]:
    return [
        ("text1 15", "text1", 15),
        ("text2 203 204", "text2 203", 204),
        ("text3 303 303", "text3 303", 303),
        ("text40", "text", 40),
        ("text", "text", None),
    ]


@pytest.fixture
def text_with_roman_page() -> list[tuple[str, str, str | None]]:
    return [
        ("text1 xi", "text1", "xi"),
        ("text2 203 v", "text2 203", "v"),
        ("text3 303 iii", "text3 303", "iii"),
        ("text4v", "text4v", None),
        ("text", "text", None),
        ("test6 i", "test6", "i"),
    ]


@pytest.fixture
def data_header_type() -> list[tuple[str, H]]:
    return [
        (".", H.NO),
        (". sample text", H.NO),
        ("2.1.1 measure space", H.DIGIT),
        ("A. brownian motion", H.ALPHABET),
        ("Contents ix", H.NO),
        ("xv", H.NO),
    ]


@pytest.fixture
def data_test_roman_pattern() -> list[tuple[Pattern, str, int | None, bool]]:
    # term1	    term2	term3
    # roman	    roman	all
    # roman	    arabic	second
    # roman	    roman	first
    # arabic    arabic	all
    # arabic	roman	second
    # arabic	arabic	first
    pat = re.compile(f"(?=\\s|^)\\s?(?P<key>[ixv]+|[IXV]+)$")
    return [
        (pat, "ix iv", None, True),
        (pat, "ix 4 4", 1, False),
        (pat, "ix iv", 0, True),
        (pat, "1 4", None, False),
        (pat, "2 v v", 1, True),
        (pat, "6 4", 0, False),
    ]


@pytest.fixture
def data_apply_roman_pattern() -> list[tuple[Pattern, str, int | None, str | list[Match]]]:
    # term1	    term2	term3
    # roman	    roman	all
    # roman	    arabic	second
    # roman	    roman	first
    # arabic    arabic	all
    # arabic	roman	second
    # arabic	arabic	first
    pat = re.compile("(?=\\s|^)\\s?(?P<key>[ixv]+|[IXV]+)$")
    return [
        (pat, "ix iv iv", None, "iv"),
        (pat, "ix 4 4", 1, []),
        (pat, "iii xxi xxi", 0, "iii"),
        (pat, "1 4 4", None, []),
        (pat, "2 v v", 1, "v"),
        (pat, "6 4 4", 0, []),
    ]


def test_ptl_separates_arabic_pages(text_with_arabic_page):
    for text, res_text, res_page in text_with_arabic_page:
        ptl = Paged_Text_Line(idx=-1, text=text)
        print(ptl)
        assert ptl.text == res_text
        assert ptl.page_number == res_page


def test_ptl_separates_roman_pages(text_with_roman_page):
    for text, res_text, res_page in text_with_roman_page:
        ptl = Paged_Text_Line(idx=-1, text=text)
        print(ptl)
        assert ptl.text == res_text
        assert ptl.roman_page_number == res_page


def test_ptl_header_type(data_header_type):
    for text, ans_header in data_header_type:
        ptl = Paged_Text_Line(idx=-1, text=text)
        read_header = ptl._get_header_type()
        print(ptl)
        assert read_header == ans_header


def test_test_pattern_at(data_test_roman_pattern):
    for pat, text, at, res in data_test_roman_pattern:
        ptl = Paged_Text_Line(idx=-1, text=text)
        print(f"at={at}")
        assert ptl.test_pattern_at(pat, at) == res


# def test_apply_pattern_at(data_apply_roman_pattern):
#     for pat, text, at, res in data_apply_roman_pattern:
#         ptl = Paged_Text_Line(idx=-1, text=text)
#         ms = ptl.apply_pattern_at(pat, at)
#         if not ptl.test_pattern_at(pat, at):
#             assert ms == res
#         else:
#             print(ptl.text)
#             print(ms)
#             assert ms[0].group("key") == res
