import os
import sys

sys.path.append(os.path.join(".", "scr"))

import pytest

# from scr.Text_Line import Paged_Text_Line
# from scr.Text_Lines import Paged_Text_Lines
from Spacer import Candidate, Insert_Space, Remove_Space  # type: ignore
from Text_Line import Paged_Text_Line  # type: ignore
from Text_Lines import Paged_Text_Lines

# from scr.Spacer import Candidate, Insert_Space
# from scr.Text_Line import Paged_Text_Line


@pytest.fixture
def data_sample_candidates_insert() -> list[tuple[str, str]]:
    return [
        ("1.3.2 答えにくい質問 (sensitiveQuestions) 9", "1.3.2 答えにくい質問 (sensitive Questions)"),
        ("1.3 1927年, RandomSamplingNumbersの本が出版される 7", "1.3 1927年, Random Sampling Numbersの本が出版される"),
        ("3.5.1 Berkson'sBias 35", "3.5.1 Berkson's Bias"),
        ("3.5.1 Berkson'sBias", "3.5.1 Berkson'sBias"),
    ]


@pytest.fixture
def data_sample_candidates_remove() -> list[tuple[str, str]]:
    return [("8. 付 録録", "8. 付録録"), ("第I章 実数と連続", "第I章 実数と連続")]


def test_candidates_insert(data_sample_candidates_insert):
    inserter = Insert_Space(Paged_Text_Lines())
    for sample, cand in data_sample_candidates_insert:
        line = Paged_Text_Line(text=sample)
        cands: list[str] = [c.text for c in inserter._get_candidates(line)]
        assert cand in cands


def test_candidates_remove(data_sample_candidates_remove):
    remover = Remove_Space(Paged_Text_Lines())
    for sample, cand in data_sample_candidates_remove:
        line = Paged_Text_Line(text=sample)
        print(remover._get_where_to_remove(line))
        cands: list[str] = [c.text for c in remover._get_candidates(line)]
        assert cand in cands
