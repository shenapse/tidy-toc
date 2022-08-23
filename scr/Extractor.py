from __future__ import annotations

import re
from re import Match, Pattern
from typing import Final, Optional

from Text_Line import Paged_Text_Line
from Text_Lines import Paged_Text_Lines


class Extractor:
    pat_digit: Final[Pattern] = re.compile(r"\d+")
    pat_abc: Final[Pattern] = re.compile(r"[a-zA-Z]")

    def __init__(self, text: list[str] | str | Paged_Text_Lines = []) -> None:
        # lines of text under edit
        if isinstance(text, Paged_Text_Lines):
            self.lines: Paged_Text_Lines = text
            return
        self.lines = Paged_Text_Lines(text)

    def is_empty(self) -> bool:
        return self.lines == []

    def read_text(self, text: list[str] | str | Paged_Text_Lines) -> None:
        self.__init__(text)

    def get_digit_only_lines(self) -> Paged_Text_Lines:
        """get pages containing no text other than page numbers"""
        return Paged_Text_Lines([line for line in self.lines if line.is_page_set() and line.get_number_of_words() == 1])

    def get_non_numbered_lines(self) -> Paged_Text_Lines:
        """get lines having no page number, arabic nor roman."""
        return Paged_Text_Lines([line for line in self.lines if not line.is_page_set()])

    def get_lines_of_text_length_one(self) -> Paged_Text_Lines:
        return Paged_Text_Lines(
            [line for line in self.lines if not line.is_page_set() and line.get_number_of_words() == 1]
        )

    def get_lines_with(self, with_word: str = "content", at_most_n_words: int = 4) -> Paged_Text_Lines:
        pat: Pattern = re.compile(with_word, re.IGNORECASE)
        return Paged_Text_Lines([line for line in self.lines if line.test_pattern_at(pat)])

    def get_lines_with_unexpected_roman_number(self) -> Paged_Text_Lines:
        """get lines that are indexed by a roman number after an arabic numbered page."""
        main_head: int = len(self.lines)
        for i, line in enumerate(self.lines):
            if line.page_number is not None:
                main_head = i
                break
        # record all front matter pages in main part
        ill_idx: list[int] = [
            i + main_head for i, line in enumerate(self.lines[main_head:]) if line.roman_page_number is not None
        ]
        return self.lines.select(ill_idx) + self._get_lines_start_with_roman_number()

    def _get_lines_start_with_roman_number(self) -> Paged_Text_Lines:
        """get lines whose text starts with roman number."""
        roman_numbered: list[int] = [
            line.idx
            for line in self.lines
            if line.header == line.Header.WORD and line.test_pattern_at(line.pat_roman_page, at=0)
        ]
        return self.lines.select(roman_numbered)

    def _get_digit_header(self, header: str) -> list[str]:
        return re.findall(self.pat_digit, header)

    def _get_abc_header(self, header: str) -> str:
        match: Optional[Match] = re.search(self.pat_abc, header)
        return match.group() if match else ""

    def _abc_in_this_order(self, abc_header1: str, abc_header2: str) -> bool:
        """test if two alphabet characters are in the incremental order."""
        return ord(abc_header1.lower()) + 1 == ord(abc_header2.lower())

    def _digits_in_this_order(self, le: list[str], r: list[str]) -> bool:
        len_min: int = min(len(le), len(r))
        for i in range(0, len_min):
            L: int = int(le[i])
            R: int = int(r[i])
            if L != R:
                return L < R
        return len(le) <= len(r)

    def get_lines_with_unexpected_header(self) -> Paged_Text_Lines:
        """get lines with suspicious header number.
        collect the latter of '13.1.5' followed by '1.31.5', or of 'B. xxx' followed by 'A. yyy',
        or of '1.1.1' followed by 'B. xxxx'.
        it ignores 'A. yyyy' followed by '2.4.1'.
        so it is generous for digit but not so for alphabet header.
        """
        # set generous init value for digit so that the next digit is easy to pass the ordering test
        digits_init: Final[list[str]] = ["0", "0", "0"]
        # set strict init value for alphabet so that the next alphabet never passes the ordering test
        abc_init: Final[str] = "{"
        digits_last: list[str] = digits_init
        abc_last: str = abc_init
        rows: list[int] = []
        for line in self.lines:
            match line.header:
                case line.Header.DIGIT:
                    # this looks like ['1','13','5']
                    digits_cur: list[str] = self._get_digit_header(line[0])
                    if not self._digits_in_this_order(digits_last, digits_cur):
                        rows.append(line.idx)
                    # record the latest digits
                    digits_last = digits_cur
                    # init back
                    abc_last = abc_init
                case line.Header.ALPHABET:
                    abc_cur: str = self._get_abc_header(line[0])
                    if not self._abc_in_this_order(abc_last, abc_cur):
                        rows.append(line.idx)
                    abc_last = abc_cur
                    # not init digit
                case line.Header.NO:
                    rows.append(line.idx)
                case line.Header.WORD:
                    continue
        return self.lines.select(rows=rows)

    def __is_well_ordered(self, a: int, b: int, c: int) -> bool:
        """is the center value b has a possible value relative to a and c.
        value 0 means it is a front page.
        value -1 a non-indexed page.
        only positive values are compared
        """
        if b <= 0:
            return True  # front and none page is ignored
        elif a <= 0 and c <= 0:  # only b is normal
            return True  # incomparable. Trivially true
        elif a <= 0:  # only a is abnormal
            return b <= c
        elif c <= 0:  # only c is abnormal
            return a <= b
        else:  # they are all normal
            return a <= b <= c

    def get_order_disturbing_main_pages(self) -> Paged_Text_Lines:
        """get lines like page-indexed (10,8,13) or (10,14,11)"""
        page_numbers: list[int] = []
        for line in self.lines:
            if not line.is_page_set():
                page_numbers.append(-1)
            elif line.roman_page_number is not None:
                page_numbers.append(0)
            elif line.page_number is not None:
                page_numbers.append(line.page_number)
        # run through page numbers list to find disturbing page
        # pick three adjacent elements to check their order consistency
        # ignore 0 since we are not interested in front matter page
        ill_page: list[Paged_Text_Line] = []
        L: Final[int] = len(page_numbers)
        INF: Final[int] = (L + 1000) * 10
        for i in range(0, L):
            cur: int = page_numbers[i]
            pre: int = page_numbers[i - 1] if i > 0 else 0
            suc: int = page_numbers[i + 1] if i < L - 1 else INF
            if not self.__is_well_ordered(pre, cur, suc):
                ill_page.append(self.lines[i])
        return Paged_Text_Lines(ill_page)
