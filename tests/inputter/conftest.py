import csv
import dataclasses
import os
import sys
from pathlib import Path
from re import Pattern

import pytest

sys.path.append(os.path.join(".", "scr"))
from Inputter import Inputter  # type: ignore

# from scr.Inputter import Inputter


@pytest.fixture
def constants():
    class constants:
        pat_none: Pattern = Inputter.Phrase.Pat.none
        pat_all: Pattern = Inputter.Phrase.Pat.all
        pat_help: Pattern = Inputter.Phrase.Pat.help
        name_none: Inputter.Phrase.Name = Inputter.Phrase.Name.NONE
        name_all: Inputter.Phrase.Name = Inputter.Phrase.Name.ALL
        name_help: Inputter.Phrase.Name = Inputter.Phrase.Name.HELP
        pat_digit: Pattern = Inputter.Digit.pat
        pat_minus: Pattern = Inputter.Minus.pat
        pat_range: Pattern = Inputter.Range.pat

    return constants


@dataclasses.dataclass
class test_data_file:
    root: Path = Path("./tests/inputter/test_case/")
    digit_ok_file = root / "digit_ok.csv"
    minus_ok_file: Path = root / "minus_ok.csv"
    range_ok_file: Path = root / "range_ok.csv"
    ng_file: Path = root / "ng.csv"
    all_ok_file: Path = root / "all.csv"
    none_file: Path = root / "none.csv"
    help_file: Path = root / "help.csv"
    word_ng_file: Path = root / "word_ng.csv"


@dataclasses.dataclass
class test_data:
    data: str
    res: list[int]


def get_test_data(file_path: Path) -> list[test_data]:
    assert file_path.exists()
    data: list[test_data] = []
    with open(str(file_path), mode="r", encoding="utf-8") as f:
        reader = csv.reader(f, skipinitialspace=True)
        for row in reader:
            res: list[int] = [] if len(row) <= 1 or row[1] == "" else [int(r) for r in row[1:]]
            data.append(test_data(data=row[0], res=res))
    return data


@pytest.fixture
def digit_ok() -> list[test_data]:
    return get_test_data(test_data_file.digit_ok_file)


@pytest.fixture
def minus_ok() -> list[test_data]:
    return get_test_data(test_data_file.minus_ok_file)


@pytest.fixture
def range_ok() -> list[test_data]:
    return get_test_data(test_data_file.range_ok_file)


@pytest.fixture
def integer_data(digit_ok, minus_ok, range_ok) -> list[test_data]:
    return digit_ok + minus_ok + range_ok


@pytest.fixture
def ng() -> list[test_data]:
    return get_test_data(test_data_file.ng_file)


@pytest.fixture
def none_ok() -> list[test_data]:
    return get_test_data(test_data_file.none_file)


@pytest.fixture
def all_ok() -> list[test_data]:
    return get_test_data(test_data_file.all_ok_file)


@pytest.fixture
def help_ok() -> list[test_data]:
    return get_test_data(test_data_file.help_file)


@pytest.fixture
def phrase_data(none_ok, all_ok, help_ok) -> list[test_data]:
    return none_ok + all_ok + help_ok
