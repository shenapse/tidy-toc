import os
import sys

import pytest

# from scr.Cleaner import Cleaner, clean_ja
# from scr.Text_Line import Paged_Text_Line
# from scr.Text_Lines import Paged_Text_Lines

sys.path.append(os.path.join(".", "scr"))
from Cleaner import Cleaner, clean_ja
from Text_Line import Paged_Text_Line
from Text_Lines import Paged_Text_Lines


def to_ptls(idx: list[int], texts: list[str]) -> Paged_Text_Lines:
    assert len(idx) == len(texts)
    idx.sort()
    return Paged_Text_Lines([Paged_Text_Line(idx[i], s) for i, s in enumerate(texts)])


@pytest.fixture
def data_cleaner() -> list[tuple[str, str]]:
    """input text + idx of expected cand"""
    return [
        ("1.1.1 Introduction:.... 1", "1.1.1 Introduction: 1"),
        ("1.1.1 Introduction:....1", "1.1.1 Introduction: 1"),
        ("1.1.1 Ideals... 22.2... cce cece eee e teenies 122", "1.1.1 Ideals 122"),
        ("1.1.1 Free......222.2... cce cece eee", "1.1.1 Free"),
        ("1.1.1 Free ......222.2... cce cece eee", "1.1.1 Free"),
    ]


@pytest.fixture
def data_cleaner_ja() -> list[tuple[list[str], str]]:
    """input text + idx of expected cand"""
    return [
        (["§3. 局所化と商体●●●79"], "§3. 局所化と商体 79"),
        (["5.2.1 定義と距離付け可能性........ ...385"], "5.2.1 定義と距離付け可能性 385"),
        (["§3 初等函数1 指数函数,三角函数……… ･・175"], "§3 初等函数1 指数函数,三角函数 175"),
        (["§4 Rn&C... ･・33"], "§4 Rn&C 33"),
    ]


def test_cleaner(data_cleaner):
    c = Cleaner()
    for data, ans in data_cleaner:
        c.read_text(data)
        cleaned_text: str = c.remove_dusts().to_text()
        print(c.get_dust_expression())
        assert cleaned_text == ans
        assert isinstance(c.lines.format_space()[0], Paged_Text_Line)


def test_cleaner_ja(data_cleaner_ja):
    for data, ans in data_cleaner_ja:
        ptls = to_ptls(idx=[1], texts=data)
        cleaned_text: str = clean_ja(ptls).to_text()
        assert cleaned_text == ans
