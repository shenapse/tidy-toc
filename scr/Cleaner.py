import abc
import re
from re import Match, Pattern
from typing import Callable

from Text_Line import Text_Line, Text_Lines


class ICleaner(metaclass=abc.ABCMeta):
    @abc.abstractclassmethod
    def __init__(self) -> None:
        self.lines: Text_Lines = Text_Lines()

    def read_text(self, text: str | list[str]):
        self.lines = Text_Lines(text)

    def read_lines(self, lines: Text_Lines | list[Text_Line]):
        if isinstance(lines, Text_Lines):
            self.lines = lines
        else:
            self.lines = Text_Lines(lines)

    def apply_each_line(
        self, pat: Pattern, func: Callable[[list[Match], Text_Line], str], skip_blank_line: bool = True
    ) -> Text_Lines:
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
                    new_lines.append(line.text)
            else:
                new_lines.append(line.text)
        return Text_Lines(new_lines)


class Cleaner(ICleaner):
    dust_phrase: str = "dust_start"

    def __init__(
        self,
        dust_pre_defined: list[str] = ["\.", "\s"],
        dust_possible: str = "[a-zA-Z0-9]",
        lead_exp: str = "(?<=[A-Z0-9\s][A-Za-z0-9\s])\S*?",
        dust_rep: int = 3,
    ) -> None:
        self.dust_major: list[str] = dust_pre_defined
        self.dust_possible: str = dust_possible
        self.lead_exp: str = lead_exp
        self.dust_rep: int = dust_rep
        self.lines: Text_Lines = Text_Lines()

    def get_dust_characters(self) -> list[str]:
        # pre-defined major pattern
        # dust pattern
        pat = re.compile(r"[A-Z].*(" + self.dust_possible + ")\\1{2,}")
        dust_redundant: list[str] = re.findall(pat, self.lines.to_text())
        dust: list[str] = []
        for d in dust_redundant:
            if d not in self.dust_major and d not in dust:
                dust.append(d)
        return dust

    def get_page_number(self, line: Text_Line) -> str:
        page_regex = "(?:[0-9]*)$|(?:[ixv]*)$|(?:[IXV]*)$"
        pat = re.compile(page_regex)
        return re.findall(pat, line.text)[0]

    def get_dust_expression(self) -> str:
        """
        get pre-regex string for leading text + dusts + page_number.
        dust + page_number part is acceptable by 'dust_start' keyword
        via Match object.
        """
        dust_care: list[str] = ["e"]
        dust_exps: list[str] = []
        for d in self.get_dust_characters():
            r: int = self.dust_rep + 1 if d in dust_care else self.dust_rep
            rep_exp: str = "{" f"{r}" + ",}"
            dust_exps.append("|".join([f"[{d}{dm}]" + rep_exp for dm in self.dust_major]))
        # dust_exps: list[str] = [
        #     "|".join([f"[{d}{dm}]" + rep_exp for dm in self.dust_major]) for d in self.get_dust_characters()
        # ]
        dust_exp = "(?P<" + Cleaner.dust_phrase + ">\s?(" + "|".join(dust_exps) + ").*)"
        # resulting pattern looks like
        # '(?<=[A-Z0-9])(\S*?)(?P<dust_phrase>\s?([e\s]{3,}|[e\.]{3,}|[\.\s]{3,}|[\.0\s]){3,}.*)()'
        return self.lead_exp + dust_exp

    def remove_dusts(self) -> Text_Lines:
        pat: Pattern = re.compile(self.get_dust_expression())

        def line_processor(m: list[Match], line: Text_Line) -> str:
            dust_border: int = m[0].start(Cleaner.dust_phrase)
            return line.text[:dust_border] + " " + self.get_page_number(line)

        return self.apply_each_line(pat, line_processor)


class Spacer(ICleaner):
    def __init__(self) -> None:
        self.lines: Text_Lines = Text_Lines()

    def remove_leading_spaces(self) -> Text_Lines:
        """remove leading spaces on each line (if exist), and return the removed lines."""
        pat: Pattern = re.compile("^\s*(?P<body>\S.*)")
        return self.apply_each_line(pat, lambda m, _: m[0].group("body"))

    def remove_tail_spaces(self) -> Text_Lines:
        """remove tail spaces on each line (if exist), and return the removed lines."""
        pat: Pattern = re.compile("(?P<body>.*\S)\s*$")
        return self.apply_each_line(pat, lambda m, _: m[0].group("body"))

    def remove_redundant_spaces(self) -> Text_Lines:
        s = Spacer()
        s.read_lines(self.remove_leading_spaces())
        return s.remove_tail_spaces()
