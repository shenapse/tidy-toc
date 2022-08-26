import itertools

import regex
from regex import Pattern

from Choose_from_Integers import Choose_from_Integers
from Mediator import Candidate, Choice, Mediator, Option
from Text_Line import Paged_Text_Line
from Text_Lines import Paged_Text_Lines


class Insert_Space(Choose_from_Integers):
    pat_need_space: Pattern = regex.compile("(?<=[a-z])[A-Z]")

    def __init__(self, lines: Paged_Text_Lines, options_max: int = 100) -> None:
        self.lines: Paged_Text_Lines = lines
        self.mediator = Mediator(public_options=["p", "r"], private_options=["f"], max_page=options_max)

    def get_rows_space_inserted(self) -> Paged_Text_Lines:
        """interactively insert space where a lower character is followed by an Upper character with no space between."""
        return self.choose_from_integers()

    def find_rows(self) -> list[Paged_Text_Line]:
        """find rows having strings in which a lower character is followed by an Upper character. e.g., ProbabilityTheory"""
        return [p for p in self.lines if p.test_pattern_at(self.pat_need_space)]

    def _get_where_to_insert(self, line: Paged_Text_Line) -> list[list[int]]:
        """get the list of positional indexes of line.text at which space might need to be inserted."""
        starts = list(
            itertools.chain.from_iterable(
                [[start for start in match.starts()] for match in regex.finditer(self.pat_need_space, line.text)]
            )
        )
        combinations: list[list[int]] = []
        for r in range(len(starts) + 1):
            combinations.extend([list(c) for c in itertools.combinations(starts, r)])
        return combinations

    def _get_candidates(self, line: Paged_Text_Line) -> list[Candidate]:
        """suggest new strings by which an input line might be replaced."""

        def insert_space(text: str, where_to_insert: list[int]) -> str:
            """get new text with space at specified index."""
            add = 0
            for c in where_to_insert:
                at: int = c + add
                text = text[:at] + " " + text[at:]
                add += 1
            return text

        return Candidate.to_candidate(
            [insert_space(text=line.text, where_to_insert=at) for at in self._get_where_to_insert(line)]
        )


class Remove_Space(Choose_from_Integers):
    pat_need_space: Pattern = regex.compile("(?<=[^\x01-\x7E部章節])[ \\s]+[^\x01-\x7E]")

    def __init__(self, lines: Paged_Text_Lines, options_max: int = 100) -> None:
        self.lines: Paged_Text_Lines = lines
        self.mediator = Mediator(public_options=["p", "r"], private_options=["f"], max_page=options_max)

    def get_rows_space_removed(self) -> Paged_Text_Lines:
        """interactively insert space where a lower character is followed by an Upper character with no space between."""
        return self.choose_from_integers()

    def find_rows(self) -> list[Paged_Text_Line]:
        """find rows having strings in which a space character lies between double-byte characters. e.g., 全角文字と 全角文字"""
        return [p for p in self.lines if p.test_pattern_at(self.pat_need_space)]

    def _get_where_to_remove(self, line: Paged_Text_Line) -> list[list[int]]:
        """get the list of positional indexes of line.text at which space might need to be inserted."""
        starts = list(
            itertools.chain.from_iterable(
                [[start for start in match.starts()] for match in regex.finditer(self.pat_need_space, line.text)]
            )
        )
        combinations: list[list[int]] = []
        for r in range(len(starts) + 1):
            combinations.extend([list(c) for c in itertools.combinations(starts, r) if c != []])
        return combinations

    def _is_trivial_candidate(self, line: Paged_Text_Line, new_text: str) -> bool:
        """check whether new_text is a worthy candidate."""
        # trivial if it is exactly the same as line
        if line.text == new_text:
            return True
        # trivial if it has digit header and has a single word part
        if line.header == line.Header.DIGIT and any(len(w) == 1 for i, w in enumerate(new_text.split()) if i > 0):
            return True
        return False

    def _get_candidates(self, line: Paged_Text_Line) -> list[Candidate]:
        """suggest new strings by which an input line might be replaced."""

        def remove_space(text: str, where_to_remove: list[int]) -> str:
            """get new text with space at specified index."""
            add = 0
            for c in where_to_remove:
                end_first: int = c + add
                start_second = end_first + 1
                text = text[:end_first] + text[start_second:]
                add -= 1
            return text

        cands: list[str] = []
        for at in self._get_where_to_remove(line):
            new_text: str = remove_space(text=line.text, where_to_remove=at)
            if not self._is_trivial_candidate(line, new_text):
                cands.append(new_text)
        return Candidate.to_candidate(cands)

    def _test_trivial_candidate(self, line: Paged_Text_Line, candidates: list[Candidate]) -> bool:
        """test if candidates for the line is too trivial for user to choose. If true, then the trivial choice is forced by some other method that follows."""
        # trivial cases
        if (L := len(candidates)) == 0:
            return True
        if L > 1:
            # trivial if line.words consists solely of single word like '推 定 法'
            return all(len(w) == 1 for i, w in enumerate(line.words) if i > 0)
        # L==1
        return True

    def _get_forced_choice(self, line: Paged_Text_Line, candidates: list[Candidate]) -> Choice:
        """decide the forced choice after candidates turn out to be trivial."""
        if (L := len(candidates)) == 0:
            return Choice(option=Option.Pass, number=0)
        elif L > 1:
            return Choice(option=Option.Fill, number=candidates[-1].idx)
        if L == 1:
            if candidates[0].text == "":
                return Choice(option=Option.Remove, number=0)
            else:
                return Choice(option=Option.Fill, number=candidates[0].idx)
        raise ValueError(f"unexpected pair of {line} and {candidates}")
