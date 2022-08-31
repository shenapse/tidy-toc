import abc
import itertools
from typing import Callable, Iterable, Optional

import regex
from regex import Match, Pattern

from Choose_from_Integers import Choose_from_Integers
from Mediator import Candidate, Choice, Mediator, Option
from Text_Line import Paged_Text_Line
from Text_Lines import Paged_Text_Lines


class ICleaner(metaclass=abc.ABCMeta):
    @abc.abstractclassmethod
    def __init__(self) -> None:
        self.dust_characters: list[str] = []
        raise NotImplementedError

    def clear_dust_characters(self) -> None:
        self.dust_characters = []

    def read_text(self, text: str | list[str]):
        self.lines = Paged_Text_Lines(text)
        self.clear_dust_characters()

    def read_lines(self, lines: Paged_Text_Lines | list[Paged_Text_Line]):
        if isinstance(lines, Paged_Text_Lines):
            self.lines = lines
        else:
            self.lines = Paged_Text_Lines(lines)
        self.clear_dust_characters()

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
        dust_pre_defined: list[str] = ["\\.", "\\s", "0", "©"],
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
        self.dust_characters: list[str] = []

    def get_dust_characters(self, rep: int = 2) -> list[str]:
        """scan whole text and find dust characters"""
        if self.dust_characters != []:
            return self.dust_characters
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
        self.pat_row: list[Pattern] = [self._generate_trailing_dust_pattern()] + [
            self._generate_weak_patterns(reps=[cleaner.dust_rep], weights=[self.cleaner.weight])[0]
        ]
        self.pats_cand: list[Pattern] = self._generate_weak_patterns() + [self._generate_trailing_dust_pattern()]
        self.mediator: Mediator = Mediator(
            public_options=[Option.Pass.value, Option.Remove.value], private_options=[Option.Digit.value], max_page=100
        )

    def _generate_weak_patterns(self, reps: list[int] = [2, 3], weights: list[int] = [0, 1]) -> list[Pattern]:
        """generate patterns of different ability to detect dust. Used for providing several options to correct words with dust."""
        return [
            regex.compile(self.cleaner.get_dust_expression(rep_default=r, add_weight=w)) for r in reps for w in weights
        ]

    def _generate_trailing_dust_pattern(self) -> Pattern:
        return regex.compile(f"[{''.join(self.cleaner.get_dust_characters() + self.cleaner.dust_major)}]+?$")

    def find_rows(self) -> Paged_Text_Lines:
        """find rows that match the dust pattern."""
        return Paged_Text_Lines(
            [line for line in self.lines if any(regex.search(pat, line.get_pure_text()) for pat in self.pat_row)]
        )

    def _is_trivial_candidate(self, line: Paged_Text_Line, start: int) -> bool:
        """check whether line.text[:start] is a worthy candidate."""
        # if it consists solely of a reliable header, it is trivial
        if line.header == line.Header.DIGIT and line[0].startswith(line.text[:start]):
            return True
        # if it is like spac[e ]
        if line.text[start:].endswith("e") or line.text[start:].endswith("s"):
            return True
        # if it detects something near header, it is very likely to be trivial
        pos, _ = line.lookup_word(start - 1) if start > 1 else (0, "")
        return pos <= 1

    def _get_candidates(self, line: Paged_Text_Line) -> list[Candidate]:
        """get candidate strings for substituting line.text."""
        candidates: set[str] = set()
        for pat in self.pats_cand:
            for match in regex.finditer(pat, line.text):
                for start in match.starts():
                    # candidate string hit by regexp
                    if not self._is_trivial_candidate(line, start):
                        candidates.add(line.text[:start])
                        # candidate words that precedes the word hit by regexp
                        word_pos, _ = line.lookup_word(start)
                        candidates.add(line.sep.join(line[:word_pos]))
        # candidates are sorted in length of their text
        return Candidate.to_candidate(sorted(candidates))

    def _test_trivial_candidate(self, line: Paged_Text_Line, candidates: list[Candidate]) -> bool:
        """test if candidates for the line is too trivial for user to choose. If true, then the trivial choice is forced by some other method that follows."""
        if (L := len(candidates)) == 0:
            return True
        if L > 1:
            return False
        # L==1
        if (c := candidates[0]).text == "" or len(c.text) >= len(line.text):
            return True
        # test if
        cand_end: int = len(c.text)
        diff: str = line.text[cand_end:]
        pat: Pattern = regex.compile(f"[^{''.join(self.cleaner.get_dust_characters() + self.cleaner.dust_major)}]")
        return regex.search(pat, diff) is None

    def _get_forced_choice(self, line: Paged_Text_Line, candidates: list[Candidate]) -> Choice:
        """decide the forced choice after candidates turn out to be trivial."""
        if (L := len(candidates)) == 0:
            return Choice(option=Option.Pass, number=0)
        if L == 1:
            if (c := candidates[0]).text == "":
                return Choice(option=Option.Remove, number=0)
            elif len(c.text) >= len(line.text):
                return Choice(option=Option.Pass, number=0)
            else:
                return Choice(option=Option.Digit, number=candidates[0].idx)
        raise ValueError(f"unexpected pair of {line} and {candidates}")

    def remove_small_dust(self) -> Paged_Text_Lines:
        """interactively remove remaining dust found in some parts of text, showing user many removal patterns."""
        return self.choose_from_integers()


class Cleaner_ja(Cleaner):
    def __init__(
        self,
        dust_pre_defined: list[str] = ["\\s", "\\.", "…", ",", "．", "，", "‥", "・", "･", "·", "●", "•", "\\-"],
        dust_possible: str = "[0-9a-zA-Z -/:-@\\[-~]",
        dust_rep: int = 3,
        weight: int = 1,
        precedes_dust_characters: str = r"[a-zA-Z\p{Script=Hiragana}\p{Script=Katakana}\p{Script=Han}]",
        precedes_dust_finder: str = r"[a-zA-Z\s:\p{Script=Hiragana}\p{Script=Katakana}\p{Script=Han}]",
        not_follow_dust_finder: str = r"[A-Z\p{Script=Hiragana}\p{Script=Katakana}\p{Script=Han}]",
    ) -> None:
        super().__init__(
            dust_pre_defined,
            dust_possible,
            dust_rep,
            weight,
            precedes_dust_characters,
            precedes_dust_finder,
            not_follow_dust_finder,
        )


class Interactive_Cleaner_ja(Interactive_Cleaner):
    def _get_candidates(self, line: Paged_Text_Line) -> list[Candidate]:
        """get candidate strings for substituting line.text."""
        candidates: set[str] = set()
        for pat in self.pats_cand:
            for match in regex.finditer(pat, line.text):
                for start in match.starts():
                    # candidate string hit by regexp
                    if not self._is_trivial_candidate(line, start):
                        candidates.add(line.text[:start])
                        # candidate words that precedes the word hit by regexp
                        # word_pos, _ = line.lookup_word(start)
                        # candidates.add(line.sep.join(line[:word_pos]))
        # candidates are sorted in length of their text
        return Candidate.to_candidate(sorted(candidates))


def clean_ja(ptls: Paged_Text_Lines) -> Paged_Text_Lines:
    c = Cleaner_ja()
    c.read_lines(ptls)
    return c.remove_dusts()
