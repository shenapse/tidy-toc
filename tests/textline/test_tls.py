import os
import sys

import pytest

# from scr.Text_Line import Text_Line, Text_Lines

sys.path.append(os.path.join(".", "scr"))
from Text_Line import Text_Line, Text_Lines  # type: ignore

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


def test_remove_blank_rows(data_remove_blank_rows):
    for data, res in data_remove_blank_rows:
        tls = Text_Lines(data)
        print(f"data={data}")
        print(f"res={res}")
        assert tls.remove_blank_rows().to_list_str() == res
