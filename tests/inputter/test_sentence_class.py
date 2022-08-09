import os
import sys

import pytest

# from scr.Interpreter import Interpreter

sys.path.append(os.path.join(".", "scr"))


from Interpreter import Interpreter  # type: ignore

#
# --------------------------------------
#   test start!
# --------------------------------------
#


@pytest.fixture
def sentence_ng() -> list[str]:
    return [
        # " start_with_space",
        # "end_with_space ",
        # "space between",
        "	start_with_tab",
        "end_with_tab	",
        "tab	between",
        "\nstart_with_newline",
        "end_with_newline\n",
        "newline\nbetween",
    ]


@pytest.fixture
def sentence_ok(integer_data, phrase_data) -> list[str]:
    integers = " ".join([d.data for d in integer_data])
    phrases = " ".join([d.data for d in phrase_data])
    msc: list[str] = [
        "normal sentence",
        "probably invalid sentence all -1",
        "multiple spaces   ",
        "very_loooooooooooooooooooooooooong_word",
    ]
    return msc + [integers] + [phrases]


def test_sentence_class_init_ng(sentence_ng):
    for s in sentence_ng:
        with pytest.raises(ValueError):
            Interpreter.Sentence(s)


def test_sentence_class_initialize_ok(sentence_ok):
    for s in sentence_ok:
        assert Interpreter.Sentence(s) == s
