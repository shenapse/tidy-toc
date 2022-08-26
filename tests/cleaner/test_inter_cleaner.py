import os
import sys

import pytest

# from scr.Cleaner import Cleaner, Interactive_Cleaner
# from scr.Text_Line import Paged_Text_Line
# from scr.Text_Lines import Paged_Text_Lines

sys.path.append(os.path.join(".", "scr"))
from Cleaner import Cleaner, Interactive_Cleaner
from Text_Line import Paged_Text_Line
from Text_Lines import Paged_Text_Lines


def to_ptls(idx: list[int], texts: list[str]) -> Paged_Text_Lines:
    assert len(idx) == len(texts)
    idx.sort()
    return Paged_Text_Lines([Paged_Text_Line(idx[i], s) for i, s in enumerate(texts)])


@pytest.fixture
def data_inter_cleaner() -> list[tuple[str, str]]:
    """input text + idx of expected cand"""
    return [
        ("1.1.1 Introduction:. 1", "1.1.1 Introduction:"),
        ("1.1.1 Introduction: .1", "1.1.1 Introduction:"),
        ("1.1.1 Introduction:.1", "1.1.1 Introduction:"),
    ]


@pytest.fixture
def data_inter_cleaner_pass() -> list[str]:
    """input text + idx of expected cand"""
    return [
        "1.1.1 Introduction",
        "1.1.1 Introduction:",
        "1.1.1 Introduction 1",
        "1.1.1 Introduction: 1",
    ]


def test_inter_cleaner(data_inter_cleaner):
    c = Cleaner()
    for data, ans in data_inter_cleaner:
        c.read_text(data)
        ptls = c.remove_dusts()
        ic = Interactive_Cleaner(cleaner=c, lines=ptls)
        print(ic.pats_cand)
        cands = [c.text for c in ic._get_candidates(Paged_Text_Line(text=data))]
        assert ans in cands


def test_inter_cleaner_pass(data_inter_cleaner_pass):
    c = Cleaner()
    for data in data_inter_cleaner_pass:
        c.read_text(data)
        ptls = c.remove_dusts()
        ic = Interactive_Cleaner(cleaner=c, lines=ptls)
        print(ic.pats_cand)
        assert ic._get_candidates(Paged_Text_Line(text=data)) == []
