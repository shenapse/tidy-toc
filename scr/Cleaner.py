import abc
import itertools
from typing import Callable, Iterable, Optional

import regex
from regex import Match, Pattern
from rich import print

from Choose_from_Integers import Choose_from_Integers
from Mediator import Candidate, Mediator
from Text_Line import Paged_Text_Line
from Text_Lines import Paged_Text_Lines


class ICleaner(metaclass=abc.ABCMeta):
    @abc.abstractclassmethod
    def __init__(self) -> None:
        raise NotImplementedError

    def read_text(self, text: str | list[str]):
        self.lines = Paged_Text_Lines(text)

    def read_lines(self, lines: Paged_Text_Lines | list[Paged_Text_Line]):
        if isinstance(lines, Paged_Text_Lines):
            self.lines = lines
        else:
            self.lines = Paged_Text_Lines(lines)

    def apply_each_line(
        self, pat: Pattern, func: Callable[[list[Match], Paged_Text_Line], str], skip_blank_line: bool = True
    ) -> Paged_Text_Lines:
        """get new lines derived by applying pat RegExp to each line and then func to the matched result.

        Args:
            pat (Pattern): applies each line to get match object
            func (Callable[[list[Match], Text_Line], str]): processes the args to output the string for a new line. Does nothing when match object is blank.

        Returns:
            Text_Lines: holds an output lines by the process.
        """
        new_lines: list[str] = []
        for line in self.lines:
            matches: list[Match] = list(regex.finditer(pat, line.text))
            if matches != []:
                new_lines.append(func(matches, line))
            elif skip_blank_line:
                if not line.is_empty():
                    new_lines.append(line.to_text())
            else:
                new_lines.append(line.to_text())
        return Paged_Text_Lines(new_lines)


class Cleaner(ICleaner):
    dust_pos: str = "dust_start"

    def __init__(
        self,
        dust_pre_defined: list[str] = ["\\.", "\\s"],
        dust_possible: str = "[a-zA-Z0-9 -/:-@\\[-~]",
        dust_rep: int = 3,
        weight: int = 1,
        precedes_dust_characters: str = "[A-Z]",
        precedes_dust_finder: str = "[a-zA-Z\\s:]",
        not_follow_dust_finder: str = "\\s?[A-Z]",
    ) -> None:
        self.dust_major: list[str] = dust_pre_defined
        self.dust_possible: str = dust_possible
        self.dust_rep: int = dust_rep
        self.weight: int = weight
        self.precedes_dust_characters: str = precedes_dust_characters
        self.precedes_dust_finder: str = precedes_dust_finder
        self.not_follow_dust_finder: str = not_follow_dust_finder
        self.lines: Paged_Text_Lines = Paged_Text_Lines()

    def get_dust_characters(self, rep: int = 2) -> list[str]:
        """scan whole text and find dust characters"""
        # pre-defined major pattern
        # dust pattern
        pat = regex.compile(f"(?<={self.precedes_dust_characters}).*?({self.dust_possible})\\1" + "{" + str(rep) + ",}")
        dust_redundant: list[str] = regex.findall(pat, self.lines.to_text(combine=False))
        return sorted(set(dust_redundant).difference(self.dust_major))

    def get_dust_expression(
        self,
        rep_default: Optional[int] = None,
        add_weight: Optional[int] = None,
        dust_care: list[str] = ["e", "s"],
    ) -> str:
        rep: int = self.dust_rep if rep_default is None else rep_default
        weight: int = self.weight if add_weight is None else add_weight

        def get_combinations(characters: list[str], r: int) -> Iterable[tuple]:
            rep: int = min(len(characters), r)
            rep = max(rep, 1)
            return itertools.combinations(characters, rep)

        def need_care(characters: Iterable[str]) -> bool:
            return len(set(dust_care) & set(characters)) != 0

        def get_rep(characters: Iterable[str]) -> int:
            return rep + weight if need_care(characters) else rep

        def get_exp(chrs: Iterable[str]) -> str:
            return f"[{''.join(chrs)}]" + "{" + f"{get_rep(chrs)}" + ",}"

        dust_exps_majors: list[str] = [get_exp(c) for c in get_combinations(self.dust_major, rep)]
        dust_exp_mixed: list[str] = [
            get_exp(list(c) + [d])
            for c in get_combinations(self.dust_major, rep - 1)
            for d in self.get_dust_characters()
        ]
        return "|".join(dust_exps_majors + dust_exp_mixed)

    def get_dust_finder(self) -> str:
        """
        get pre-regex string for leading text + dusts + page_number.
        dust + page_number part is accessible by 'dust_start' keyword
        via Match object.
        """
        dust_exp: str = f"(?=\\s?{self.get_dust_expression()})"
        return (
            f"(?<={self.precedes_dust_finder})"
            + dust_exp
            + f"(?P<{self.dust_pos}>.*)"
            + f"(?!{self.not_follow_dust_finder})"
        )

    def remove_dusts(self) -> Paged_Text_Lines:
        pat: Pattern = regex.compile(self.get_dust_finder())

        def line_processor(ms: list[Match], line: Paged_Text_Line) -> str:
            dust_border: int = min([m.start(Cleaner.dust_pos) for m in ms])
            return line.text[:dust_border] + " " + line.get_page_string()

        return self.apply_each_line(pat, line_processor)


class Interactive_Cleaner(Choose_from_Integers):
    def __init__(self, cleaner: Cleaner, lines: Paged_Text_Lines) -> None:
        self.cleaner: Cleaner = cleaner
        self.lines: Paged_Text_Lines = lines
        self.pat_row: Pattern = self._generate_patterns(reps=[cleaner.dust_rep], weights=[self.cleaner.weight])[0]
        self.pats_cand: list[Pattern] = self._generate_patterns()
        self.mediator: Mediator = Mediator(public_options=["p", "r"], private_options=["f"], max_page=100)

    def _generate_patterns(self, reps: list[int] = [2, 3], weights: list[int] = [0, 1]) -> list[Pattern]:
        """generate patterns of different ability to detect dust. Used for providing several options to correct words with dust."""
        return [
            regex.compile(self.cleaner.get_dust_expression(rep_default=r, add_weight=w)) for r in reps for w in weights
        ]

    def find_rows(self) -> Paged_Text_Lines:
        """find rows that match the dust pattern."""
        return Paged_Text_Lines([line for line in self.lines if line.test_pattern_at(self.pat_row)])

    def _get_candidates(self, line: Paged_Text_Line) -> list[Candidate]:
        """get candidate strings for substituting line.text."""
        candidates: set[str] = set()
        for pat in self.pats_cand:
            for match in regex.finditer(pat, line.text):
                dust_pos: int = match.start(0)
                # candidate string hit by regexp
                candidates.add(line.text[:dust_pos])
                # candidate words that precedes the word hit by regexp
                word_pos, _ = line.lookup_word(dust_pos)
                candidates.add(line.sep.join(line[:word_pos]))
                # candidates are sorted in length of their text
        return Candidate.to_candidate(sorted(candidates))

    def remove_small_dust(self) -> Paged_Text_Lines:
        """interactively remove remaining dust found in some parts of text, showing user many removal patterns."""
        return self.choose_from_integers()


def clean_ja(ptls: Paged_Text_Lines) -> Paged_Text_Lines:
    c = Cleaner(
        dust_pre_defined=["\\s", "\\.", "…", ",", "．", "，", "‥", "・", "･", "●"],
        dust_possible="[0-9a-zA-Z -/:-@\\[-~]",
        precedes_dust_characters=r"[a-zA-Z\p{Script=Hiragana}\p{Script=Katakana}\p{Script=Han}]",
        precedes_dust_finder=r"[a-zA-Z\s:\p{Script=Hiragana}\p{Script=Katakana}\p{Script=Han}]",
        not_follow_dust_finder=r"[A-Z\p{Script=Hiragana}\p{Script=Katakana}\p{Script=Han}]",
    )
    c.read_lines(ptls)
    print(c.get_dust_expression())
    return c.remove_dusts()
