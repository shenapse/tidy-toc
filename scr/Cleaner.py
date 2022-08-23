import abc
import re
from dataclasses import dataclass
from enum import IntEnum
from re import Match, Pattern
from typing import Callable, Final, Optional

import click
from rich import print
from typing_extensions import Self

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
            matches: list[Match] = list(re.finditer(pat, line.text))
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
        dust_possible: str = "[a-zA-Z0-9]",
        lead_exp: str = "(?P<dust_start>[^A-Z])(?<![A-Z])[^A-Z]*?\\s?",
        dust_rep: int = 3,
        weight: int = 1,
    ) -> None:
        self.dust_major: list[str] = dust_pre_defined
        self.dust_possible: str = dust_possible
        self.lead_exp: str = lead_exp
        self.dust_rep: int = dust_rep
        self.weight: int = weight
        self.lines: Paged_Text_Lines = Paged_Text_Lines()

    def get_dust_characters(self) -> list[str]:
        """scan whole text and find dust characters"""
        # pre-defined major pattern
        # dust pattern
        pat = re.compile("(?<=[A-Z]).*?" + "(" + f"{self.dust_possible}" + ")\\1{2,}")
        dust_redundant: list[str] = re.findall(pat, self.lines.to_text(combine=False))
        return sorted(set(dust_redundant).difference(self.dust_major))

    def get_dust_expression(
        self,
        rep_default: Optional[int] = None,
        add_weight: Optional[int] = None,
        dust_care: list[str] = ["e", "s"],
    ) -> str:
        """get pre-regexp string for dust pattern.
        the pattern are generated in a greedy way by those characters that appear too frequently somewhere in the whole text."""
        rep: int = self.dust_rep if rep_default is None else rep_default
        weight: int = self.weight if add_weight is None else add_weight

        def _get_repeat_exp(dust1: str, dust2: str) -> str:
            # prevent words end with double 's' and 'e' such as "Fr[ee ]", "Succe[ss ]" from being hit
            r: int = rep + weight if dust1 in dust_care or dust2 in dust_care else rep
            rep_exp: str = "{" + f"{r}" + ",}"
            return f"[{dust1}{dust2}]{rep_exp}"  # like [\\t,\\.]{3,}

        dust_exps: list[str] = []
        # first, craft dust patterns from pre-defined dust pattern
        for i, d1 in enumerate(self.dust_major):
            for j, d2 in enumerate(self.dust_major):
                if i > j:
                    dust_exps.append(
                        _get_repeat_exp(
                            dust1=d1,
                            dust2=d2,
                        )
                    )
        for d in self.get_dust_characters():
            dust_exps.append("|".join([_get_repeat_exp(d, dm) for dm in self.dust_major]))
        # resulting pattern looks like
        # [\s\.]{3,}|[0\.]{3,}|...|[e\s]{4,}
        return "|".join(dust_exps)

    def get_dust_finder(self, precede: str = "(?<=[a-zA-Z\\s:])", not_follow: str = "(?!\\s?[A-Z])") -> str:
        """
        get pre-regex string for leading text + dusts + page_number.
        dust + page_number part is accessible by 'dust_start' keyword
        via Match object.
        """
        dust_exp: str = f"(?=\\s?{self.get_dust_expression()})"
        return precede + dust_exp + f"(?P<{self.dust_pos}>.*)" + not_follow

    def remove_dusts(self) -> Paged_Text_Lines:
        pat: Pattern = re.compile(self.get_dust_finder())

        def line_processor(ms: list[Match], line: Paged_Text_Line) -> str:
            dust_border: int = min([m.start(Cleaner.dust_pos) for m in ms])
            return line.text[:dust_border] + " " + line.get_page_string()

        return self.apply_each_line(pat, line_processor)


class Interactive_Cleaner:
    _highlight: Final[str] = "magenda"

    class Choice(IntEnum):
        Remove = -1
        Skip = 0

        @classmethod
        def values(cls) -> list[int]:
            return [c.value for c in cls]

        @classmethod
        def lookup(cls, x: int) -> Self:
            for c in cls:
                if c == x:
                    return c
            raise ValueError(f"x={x} points nothing in {cls.__name__} whose values are {cls.values()}.")

        @classmethod
        def generate_msg(cls, choice: int) -> str:
            match choice:
                case -1:
                    return "Remove this row."
                case 0:
                    return "Skip"
                case _:
                    raise ValueError(
                        f"choice={choice} points nothing in {cls.__name__} whose values are {cls.values()}."
                    )

    @dataclass
    class Option:
        msg: str
        idx: int

    def __init__(self, cleaner: Cleaner, lines: Paged_Text_Lines) -> None:
        self.cleaner: Cleaner = cleaner
        self.pat_row: Pattern = self._generate_patterns(reps=[cleaner.dust_rep], weights=[self.cleaner.weight])[0]
        self.pats_cand: list[Pattern] = self._generate_patterns()
        self.lines: Paged_Text_Lines = lines

    def _generate_patterns(self, reps: list[int] = [2, 3], weights: list[int] = [0, 1]) -> list[Pattern]:
        """generate patterns of different ability to detect dust. Used for providing several options to correct words with dust."""
        return [
            re.compile(self.cleaner.get_dust_expression(rep_default=r, add_weight=w)) for r in reps for w in weights
        ]

    def find_rows(self) -> Paged_Text_Lines:
        """find rows that match the dust pattern."""
        return Paged_Text_Lines([line for line in self.lines if line.test_pattern_at(self.pat_row)])

    def _generate_color_block(self) -> tuple[str, str]:
        return f"[{self._highlight}/]", "[/]"

    def _get_candidates(self, line: Paged_Text_Line) -> list[str]:
        """get candidate strings for substituting line.text."""
        candidates: set[str] = set()
        for pat in self.pats_cand:
            for match in re.finditer(pat, line.text):
                dust_pos: int = match.start(0)
                # candidate string hit by regexp
                candidates.add(line.text[:dust_pos])
                # candidate that's present before the word hit by regexp
                word_pos, _ = line.lookup_word(dust_pos)
                candidates.add(line.sep.join(line[:word_pos]))
        return sorted(candidates)

    def _show_options(self, options: list[Option]) -> None:
        """print correction candidates (for a given row with dust)."""
        begin, end = self._generate_color_block()
        display: str = "\n".join([f"{begin}N={o.idx}{end} | {o.msg}" for o in options])
        print(display)

    def _get_chosen_option(self, options: list[Option]) -> Option:
        """ask user to choose from the option. options are expressed by integers -1,0,1,..."""
        max: int = len(options)
        user_input: int = click.prompt(text="choose N", type=click.IntRange(-1, max), default=1)
        return self._find_option(options=options, user_choice=user_input)

    def _find_option(self, options: list[Option], user_choice: int) -> Option:
        for option in options:
            if user_choice == option.idx:
                return option
        sep = "\n"
        raise ValueError(
            f"no option is found with idx={user_choice} in option={sep.join([str(option) for option in options])}"
        )

    def _interpret(self, option: Option) -> int | Choice:
        return self.Choice.lookup(option.idx) if option.idx in Interactive_Cleaner.Choice.values() else option.idx

    def _generate_user_options(self, candidates: list[str]) -> list[Option]:
        options_c = self._generate_predefined_options()
        start: int = max([o.idx for o in options_c]) + 1
        return options_c + [self.Option(msg=c, idx=i + start) for i, c in enumerate(candidates)]

    def _generate_predefined_options(self) -> list[Option]:
        return [self.Option(msg=self.Choice.generate_msg(c), idx=c.value) for c in Interactive_Cleaner.Choice]

    def remove_small_dust(self) -> Paged_Text_Lines:
        lines_to_replace: list[Paged_Text_Line] = []
        lines_to_delete: list[int] = []
        for line in self.find_rows():
            candidates: list[str] = self._get_candidates(line)
            options: list[Interactive_Cleaner.Option] = self._generate_user_options(candidates)
            self._show_options(options)
            # let user choose from them
            # interpret the user choice
            option = self._get_chosen_option(options=options)
            user_choice: int | Interactive_Cleaner.Choice = self._interpret(option)
            if isinstance(user_choice, int):
                # user
                line.text = option.msg
                lines_to_replace.append(line)
            elif user_choice == self.Choice.Remove:
                # delete
                lines_to_delete.append(line.idx)
        return self.lines.exclude(lines_to_delete).overwrite(lines_to_replace)
