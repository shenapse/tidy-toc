import abc
import re
from re import Match, Pattern
from typing import Callable

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
    ) -> None:
        self.dust_major: list[str] = dust_pre_defined
        self.dust_possible: str = dust_possible
        self.lead_exp: str = lead_exp
        self.dust_rep: int = dust_rep
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
        what_precede: str = "(?<=[a-zA-Z\\s:])",
        what_not_follow: str = "(?!\\s?[A-Z])",
        rep_default: int = 3,
        add_weight: int = 1,
        dust_care: list[str] = ["e", "s"],
    ) -> str:
        """
        get pre-regex string for leading text + dusts + page_number.
        dust + page_number part is accessible by 'dust_start' keyword
        via Match object.
        """

        def _get_repeat_exp(dust1: str, dust2: str) -> str:
            # prevent words end with double 's' and 'e' such as "Fr[ee ]", "Succe[ss ]" from being hit
            r: int = rep_default + add_weight if dust1 in dust_care or dust2 in dust_care else rep_default
            rep_exp: str = "{" + f"{r}" + ",}"
            return f"[{dust1}{dust2}]{rep_exp}"  # like [\\s,\\.]{3,}

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
        dust_exp = f'(?=\\s?{"|".join(dust_exps)})'
        # resulting pattern looks like
        # (?<=[a-zA-Z\s])(?=\s?[\s\.]{3,}|[0\.]{3,}|...|[e\s]{4,})(?!\s?[A-Z]).*
        return what_precede + dust_exp + f"(?P<{self.dust_pos}>.*)" + what_not_follow

    def remove_dusts(self) -> Paged_Text_Lines:
        pat: Pattern = re.compile(self.get_dust_expression())

        def line_processor(ms: list[Match], line: Paged_Text_Line) -> str:
            dust_border: int = min([m.start(Cleaner.dust_pos) for m in ms])
            return line.text[:dust_border] + " " + line.get_page_string()

        return self.apply_each_line(pat, line_processor)
