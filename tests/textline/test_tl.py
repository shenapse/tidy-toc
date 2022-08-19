import os
import sys
from cgi import test

import pytest

# from scr.Text_Line import Text_Line, Text_Lines

sys.path.append(os.path.join(".", "scr"))
from Text_Line import Text_Line  # type: ignore
from Text_Lines import Text_Lines

#
# -------------------------
#   test start!
# -------------------------

# ---------------------------------------------
# pict_tl.txt
# ---------------------------------------------
# term1   term2   term3   term4   term5
# ----------------------------------------------
# space   space   space   nl      text      OK
# text    text    space   nl      space     OK
# nl      nl      text    nl      space     OK
# text    text    text    text    nl        OK
# nl      space   text    text    nl        OK
# space   text    text    space   text      OK
# nl      space   space   space   nl        OK
# text    space   nl      space   space     OK
# space   nl      nl      space   nl        OK
# --------------------------------------------
# space   nl      space   text    space     NG
# nl      text    nl      text    text      NG
# text    nl      nl      nl      text      NG
# text    nl      text    nl      nl        NG
# ---------------------------------------------


@pytest.fixture
def textline_data_ng() -> list[str]:
    texts: list[str] = ["tsn \n ts ", "\n n\nntt", "tnnn\n\n\nt", "t\ntnn\n\n"]
    return texts


@pytest.fixture
def textline_data_ok() -> list[str]:
    texts: list[str] = [
        "   \nsssnt",
        "ttsns \n ",
        "\n\nnntns\n ",
        "ttttn\n",
        "\n nsttn\n",
        " stts t",
        "\n   \n",
        "tsnss \n  ",
        " \n snst ",
        " \n\n \n",
    ]
    return texts


@pytest.fixture
def textline_empty() -> list[str]:
    texts: list[str] = [
        "\n   \n",
        " \n\n \n",
    ]
    return texts


@pytest.fixture
def words_get_single_ok() -> list[tuple[str, int, str]]:
    text: str = "0 1 2 3 4 5"
    return [
        (text, 0, "0"),
        (text, 1, "1"),
        (text, 5, "5"),
        (text, -1, "5"),
        (text, -2, "4"),
    ]


@pytest.fixture
def words_get_single_ng() -> list[tuple[str, int]]:
    text: str = "10 9 8 7 6"
    return [(text, 6), (text, -6)]


@pytest.fixture
def words_set_single_ok() -> list[tuple[str, int, str, str]]:
    text: str = "0 1 2 3 4 5"
    return [
        (text, 0, "1", "1 1 2 3 4 5"),
        (text, 1, "2", "0 2 2 3 4 5"),
        (text, 5, "4", "0 1 2 3 4 4"),
        (text, -1, "1", "0 1 2 3 4 1"),
        (text, -2, "1", "0 1 2 3 1 5"),
    ]


def test_textline_ok(textline_data_ok):
    for i, text in enumerate(textline_data_ok):
        T = Text_Line(idx=i, text=text)
        assert T.text == text.strip()


def test_textline_ng(textline_data_ng):
    for i, text in enumerate(textline_data_ng):
        with pytest.raises(ValueError):
            print([text])
            Text_Line(idx=i, text=text)


def test_textline_empty(textline_empty):
    for i, text in enumerate(textline_empty):
        print([text])
        T = Text_Line(idx=i, text=text)
        assert T.is_empty()


def test_textline_get_single_item_ok(words_get_single_ok):
    for text, idx, ans in words_get_single_ok:
        tl = Text_Line(idx=-1, text=text)
        print(tl)
        assert tl[idx] == ans


def test_textline_get_single_item_ng(words_get_single_ng):
    for text, idx in words_get_single_ng:
        tl = Text_Line(idx=-1, text=text)
        print(tl)
        print(idx)
        with pytest.raises(IndexError):
            print(tl[idx])


def test_textline_slice():
    data: list[str] = [str(i) for i in range(10)]
    test_data: str = " ".join(data)
    tl = Text_Line(idx=-1, text=test_data)
    assert tl[:] == data
    assert tl[:1] == data[:1]
    assert tl[8:] == data[8:]
    assert tl[2:5] == data[2:5]
    assert tl[1:3:2] == data[1:3:2]


def test_textline_set_single_item(words_set_single_ok):
    for text, idx, value, ans in words_set_single_ok:
        tl = Text_Line(idx=-1, text=text)
        print(tl)
        tl[idx] = value
        assert tl.text == ans
