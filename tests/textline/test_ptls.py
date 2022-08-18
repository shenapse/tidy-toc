import os
import sys

import pytest

sys.path.append(os.path.join(".", "scr"))
from Text_Line import Paged_Text_Line, Text_Line  # type: ignore
from Text_Lines import Paged_Text_Lines, Text_Lines, _Text_Lines


def to_ptls(idx: list[int], text: str = "text") -> Paged_Text_Lines:
    return Paged_Text_Lines([Paged_Text_Line(idx=i, text=text) for i in idx])


@pytest.fixture
def data_select() -> list[tuple[Paged_Text_Lines, list[int], list[int]]]:
    data_and_res = [
        (to_ptls(idx=[1, 2, 3], text="before"), [2, 3], [2, 3]),
        (to_ptls(idx=[5], text="before"), [2, 3], []),
        (to_ptls(idx=[1], text="before"), [1, 2, 3], [1]),
        (to_ptls(idx=[1], text="before"), [], []),
        (Paged_Text_Lines(), [1], []),
        (Paged_Text_Lines(), [], []),
    ]
    return data_and_res


def test_select_ptls(data_select):
    for before, rows, ans in data_select:
        ptls = before.select(rows)
        print(ptls)
        idx_calc: list[int] = ptls.get_index()
        assert idx_calc == ans
        assert isinstance(ptls, Paged_Text_Lines)
