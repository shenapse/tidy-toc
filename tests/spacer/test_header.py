import os
import sys

sys.path.append(os.path.join(".", "scr"))

import pytest

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
    return [("§1, 集合と写像", "§1. 集合と写像"), ("§27. 線型近似", "§27. 線型近似")]


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


def test_well_aligned(data_well_aligned):
    for text, ans in data_well_aligned:
        al = Header_Aligner(lines=Paged_Text_Lines(text), sep=".", header_symbol="§")
        print(text)
        assert al.is_aligned(line=Paged_Text_Line(text=text)) == ans


def test_replace_sep(data_replace_sep):
    for text, ans in data_replace_sep:
        al = Header_Aligner(lines=Paged_Text_Lines(text), sep=".", header_symbol="§")
        print(text)
        print(al.pat_sep_possible)
        assert al.replace_sep(text) == ans


def test_align(data_aligned):
    for text, ans in data_aligned:
        al = Header_Aligner(lines=Paged_Text_Lines(text), sep=".", header_symbol="§")
        assert ans in al._get_aligned(text)
