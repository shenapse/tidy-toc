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
def word_ng() -> list[str]:
    return [
        "",
        " start_with_space",
        "end_with_space ",
        "space between",
        "	start_with_tab",
        "end_with_tab	",
        "tab	between",
        "\nstart_with_newline",
        "end_with_newline\n",
        "newline\nbetween",
    ]


def test_word_class_initialize_ng(word_ng):
    for s in word_ng:
        with pytest.raises(ValueError):
            Interpreter.Word(s)


def test_word_class_initialize_ok(integer_data, phrase_data):
    ok_sample = [d.data for d in (integer_data + phrase_data)]
    for s in ok_sample:
        assert Interpreter.Word(s) == s
