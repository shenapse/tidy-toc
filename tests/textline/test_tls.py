import os
import sys

import pytest

# from scr.Text_Line import Text_Line, Text_Lines

sys.path.append(os.path.join(".", "scr"))
from Text_Line import Text_Line  # type: ignore
from Text_Lines import Text_Lines

#
# -------------------------
#   test start!
# -------------------------


@pytest.fixture
def data_remove_blank_rows() -> list[tuple[list[str], list[str]]]:
    t: str = "text"
    b: str = ""
    # t t t
    # t b t
    # t b b
    # b b b
    data_and_res = [
        ([t, t, t], [t, t, t]),
        ([t, b, t], [t, t]),
        (
            [t, b, b],
            [
                t,
            ],
        ),
        ([b, b, b], []),
    ]
    return data_and_res


def to_textlines(idx: list[int], text: str = "text") -> Text_Lines:
    return Text_Lines([Text_Line(idx=i, text=text) for i in idx])


@pytest.fixture
def data_select() -> list[tuple[Text_Lines, list[int], list[int]]]:
    data_and_res = [
        (to_textlines(idx=[1, 2, 3], text="before"), [2, 3], [2, 3]),
        (to_textlines(idx=[5], text="before"), [2, 3], []),
        (to_textlines(idx=[1], text="before"), [1, 2, 3], [1]),
        (to_textlines(idx=[1], text="before"), [], []),
        (Text_Lines(), [1], []),
        (Text_Lines(), [], []),
    ]
    return data_and_res


@pytest.fixture
def data_overwrite() -> list[tuple[Text_Lines, Text_Lines, list[int]]]:
    """input two text lines + expected idx for 'after'"""
    data_and_res = [
        (to_textlines(idx=[1, 2, 3], text="before"), to_textlines(idx=[2, 3], text="after"), [2, 3]),
        (to_textlines(idx=[5], text="before"), to_textlines(idx=[2, 3], text="after"), [2, 3]),
        (to_textlines(idx=[2, 3], text="before"), to_textlines(idx=[5], text="after"), [5]),
        (to_textlines(idx=[1], text="before"), to_textlines(idx=[1, 2, 3], text="after"), [1, 2, 3]),
        (to_textlines(idx=[1], text="before"), Text_Lines(), []),
        (Text_Lines(), to_textlines(idx=[1], text="after"), [1]),
        (Text_Lines(), Text_Lines(), []),
    ]
    return data_and_res


@pytest.fixture
def data_add() -> list[tuple[Text_Lines, Text_Lines, list[int]]]:
    """input two text lines + expected idx for 'after'"""
    data_and_res = [
        (to_textlines(idx=[1, 2, 3], text="before"), to_textlines(idx=[2, 3], text="after"), [1, 2, 3]),
        (to_textlines(idx=[2, 3], text="before"), to_textlines(idx=[1, 2, 3], text="after"), [1, 2, 3]),
        (to_textlines(idx=[5], text="before"), to_textlines(idx=[2, 3], text="after"), [2, 3, 5]),
        (to_textlines(idx=[2, 3], text="before"), to_textlines(idx=[5], text="after"), [2, 3, 5]),
        (to_textlines(idx=[1], text="before"), Text_Lines(), [1]),
        (Text_Lines(), Text_Lines(), []),
    ]
    return data_and_res


@pytest.fixture
def data_exclude() -> list[tuple[Text_Lines, list[int], list[int]]]:
    """input two text lines + expected idx for 'after'"""
    data_and_res = [
        (to_textlines(idx=[1, 2, 3], text="before"), [2, 3], [1]),
        (to_textlines(idx=[2, 3], text="before"), [1, 2, 3], []),
        (to_textlines(idx=[5], text="before"), [2, 3], [5]),
        (to_textlines(idx=[2, 3], text="before"), [5], [2, 3]),
        (to_textlines(idx=[1], text="before"), [], [1]),
        (Text_Lines(), [], []),
    ]
    return data_and_res


def test_select_textlines(data_select):
    for before, rows, ans in data_select:
        tls = before.select(rows)
        idx_calc: list[int] = tls.get_index()
        print(tls)
        assert idx_calc == ans


def test_remove_blank_rows(data_remove_blank_rows):
    for data, res in data_remove_blank_rows:
        tls = Text_Lines(data)
        print(f"data={data}")
        print(f"res={res}")
        assert tls.remove_blank_rows().to_list_str() == res


def test_merge_textlines(data_overwrite):
    for before, after, ans in data_overwrite:
        tls = before.overwrite(after)
        idx_calc: list[int] = [tl.idx for tl in tls if tl.text == "after"]
        print(tls)
        assert idx_calc == ans


def test_add_textlines(data_add):
    for before, after, ans in data_add:
        tls = before + after
        idx_calc: list[int] = tls.get_index()
        print(tls)
        assert idx_calc == ans


def test_exclude_textlines(data_exclude):
    for tls, idx, ans in data_exclude:
        tls_after = tls.exclude(idx)
        idx_calc: list[int] = tls_after.get_index()
        print(tls)
        assert idx_calc == ans
