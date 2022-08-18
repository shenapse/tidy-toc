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


# def test_remove_leading_spaces_ok():
#     pass


# def test_remove_tail_spaces_ng():
#     pass


# def test_remove_tal_spaces_ok():
#     pass


# def test_remove_blank_line_ng():
#     pass


# def test_remove_blank_line_ok():
#     pass
