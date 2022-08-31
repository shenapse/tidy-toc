import os
import sys

sys.path.append(os.path.join(".", "scr"))
import pytest
import regex

# from scr.Spacer import Candidate, Header_Aligner, Insert_Space, Remove_Space
# from scr.Text_Line import Paged_Text_Line
# from scr.Text_Lines import Paged_Text_Lines
from Spacer import Candidate, Header_Aligner, Insert_Space, Remove_Space  # type: ignore
from Text_Line import Paged_Text_Line  # type: ignore
from Text_Lines import Paged_Text_Lines


@pytest.fixture
def data_well_aligned() -> list[tuple[str, bool]]:
    return [
        ("§1. 集合と写像", True),
        ("§1.1 集合と写像", True),
        ("§1.1. 集合と写像", True),
        ("§1.. 集合と写像", True),
        ("§ 1. 集合と写像", False),
        ("§1. 1 集合と写像", False),
        ("§1.1 . 集合と写像", False),
    ]


@pytest.fixture
def data_replace_sep() -> list[tuple[str, str]]:
    return [("§10,1. 集合と写像, hoge", "§10.1. 集合と写像, hoge"), ("§27..1. 線型近似", "§27.1. 線型近似")]


@pytest.fixture
def data_aligned() -> list[tuple[str, str]]:
    return [
        ("§1. 集合と写像", "§1. 集合と写像"),
        ("§1.1 集合と写像", "§1.1 集合と写像"),
        ("§1.1. 集合と写像", "§1.1. 集合と写像"),
        ("§1.. 集合と写像", "§1.. 集合と写像"),
        ("§ 1. 集合と写像", "§1. 集合と写像"),
        ("§1. 1 集合と写像", "§1.1 集合と写像"),
        ("§1.1 . 集合と写像", "§1.1. 集合と写像"),
    ]


@pytest.fixture
def data_aligned_without_header() -> list[tuple[str, str]]:
    return [
        ("1. 集合と写像", "1. 集合と写像"),
        ("1.1 集合と写像", "1.1 集合と写像"),
        ("1.1. 集合と写像", "1.1. 集合と写像"),
        ("1.. 集合と写像", "1.. 集合と写像"),
        (" 1. 集合と写像", "1. 集合と写像"),
        ("1. 1 集合と写像", "1.1 集合と写像"),
        ("1.1 . 集合と写像", "1.1. 集合と写像"),
    ]


@pytest.fixture
def data_test_raw_cands() -> list[tuple[str, str]]:
    return [
        # ("§1. 2-dim", "§1. 2-dim"),
        ("1 , 2-dim", "1. 2-dim"),
        ("1.1 2-dim", "1.1 2-dim"),
        ("1 2-dim", "1 2-dim"),
    ]


@pytest.fixture
def data_is_digit_place_undecidable() -> list[tuple[str, bool]]:
    return [
        # ("§1. 2-dim", "§1. 2-dim"),
        ("1 , 2-dim", True),
        ("1 2-dim", True),
        ("1.1 dim", False),
        ("1,1 dim", False),
        ("1, dim", False),
        ("1. dim", False),
    ]


def test_aligned(data_well_aligned):
    for text, ans in data_well_aligned:
        al = Header_Aligner(lines=Paged_Text_Lines(text), sep=".", header_symbol="§")
        print(text)
        assert al.is_aligned(line=Paged_Text_Line(text=text)) == ans


def test_replace_sep(data_replace_sep):
    for text, ans in data_replace_sep:
        al = Header_Aligner(lines=Paged_Text_Lines(text), sep=".", header_symbol="§")
        print(text)
        print(al.pat_replace_sep)
        assert al.replace_sep(text) == ans


def test_align(data_aligned):
    for text, ans in data_aligned:
        al = Header_Aligner(lines=Paged_Text_Lines(text), sep=".", header_symbol="§")
        assert ans in al._get_aligned(text)


def test_align_without_header(data_aligned_without_header):
    for text, ans in data_aligned_without_header:
        al = Header_Aligner(lines=Paged_Text_Lines(text), sep=".", header_symbol="")
        assert ans in al._get_aligned(text)


def test_is_digit_place_undecidable(data_is_digit_place_undecidable):
    for text, ans in data_is_digit_place_undecidable:
        al = Header_Aligner(lines=Paged_Text_Lines(text), sep=".", header_symbol="")
        assert al._is_digit_place_undecidable(text) == ans
