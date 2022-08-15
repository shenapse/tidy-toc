from __future__ import annotations

import re
from enum import IntEnum, auto
from typing import Final

from Text_Line import Text_Line, Text_Lines


class Extractor:
    class Header(IntEnum):
        DIGIT = auto()
        ALPHABET = auto()
        NEITHER = auto()

    def __init__(self, text: list[str] | str | Text_Lines = []) -> None:
        # lines of text edit
        self.lines: Text_Lines = Text_Lines()
        if isinstance(text, Text_Lines):
            self.lines = text
        elif isinstance(text, (list, str)):
            self.lines = Text_Lines(text)
        else:
            raise TypeError(f"Unexpected input for Extractor.__init__(). text={text}")

    def is_empty(self) -> bool:
        return self.lines == []

    def read_text(self, text: str | list[str] | Text_Lines) -> None:
        self.__init__(text)

    def get_digit_only_lines(self) -> Text_Lines:
        """get pages containing no text other than page numbers"""
        pat = re.compile("^[0-9\\s]+$|^[ixv\\s]+$|^[IXV\\s]+$")
        ret: Text_Lines = Text_Lines()
        for line in self.lines:
            found = re.findall(pat, line.text)
            if found != []:
                ret.append(line)
        return ret

    def get_page_number(self, line: Text_Line) -> str:
        """get the page number located in the tail of the input string line. Might be an empty string."""
        page_regex = "(?:\\s[0-9]*)$|(?:\\s[ixv]*)$|(?:\\s[IXV]*)$"
        pat = re.compile(page_regex)
        matches: list[str] = re.findall(pat, line.text)
        return matches[0] if matches != [] else ""

    def has_page_number(self, line: Text_Line) -> bool:
        return (num := self.get_page_number(line)) != "" and num != " "

    def test_front_matter_number(self, text: str) -> bool:
        return re.findall(r"\s?[ixv]+|\s?[IXV]+", text) != []

    def is_front_matter(self, line: Text_Line) -> bool:
        """
        yes if line has a page number like iii or iv or xii.
        no if 1 or 50 or 100.
        error if otherwise
        """
        if not self.has_page_number(line):
            raise Exception("No page number found.")
        return re.findall(r"\s?[ixv]+$|\s?[IXV]+$", line.text) != []

    def get_non_numbered_pages(self) -> Text_Lines:
        return Text_Lines([line for line in self.lines if not self.has_page_number(line)])

    def get_unexpected_front_matter_lines(self) -> Text_Lines:
        """get lines that are indexed by a roman number after an arabic numbered page."""
        main_head: int = 0
        for i, line in enumerate(self.lines):
            if not self.has_page_number(line):
                continue
            elif not self.is_front_matter(line):
                main_head = i
                break
        # record all front matter pages in main part
        ill_idx: list[int] = [
            i + main_head
            for i, line in enumerate(self.lines[main_head:])
            if self.has_page_number(line) and self.is_front_matter(line)
        ]
        return Text_Lines(self.lines).select(ill_idx) + self._get_pages_start_with_front_matter_number()

    def _get_pages_start_with_front_matter_number(self) -> Text_Lines:
        front_numbered: list[int] = [
            line.idx for line in self.lines if self.test_front_matter_number(line.get_words_at(0))
        ]
        return self.lines.select(front_numbered)

    def _get_header_type(self, header: str) -> Header:
        if re.findall(r"\d+", header) != []:
            return self.Header.DIGIT
        elif re.findall(r"[a-zA-Z]", header) != []:
            return self.Header.ALPHABET
        return self.Header.NEITHER

    def _get_digit_header(self, header: str) -> list[str]:
        return re.findall(r"\d+", header)

    def _get_abc_header(self, header: str) -> str:
        return re.findall(r"[a-zA-Z]", header)[0]

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

    def get_lines_with_unexpected_header(self) -> Text_Lines:
        """get lines with suspicious header number.
        collect the latter of '13.1.5' followed by '1.31.5', or of 'B. xxx' followed by 'A. yyy',
        or of '1.1.1' followed by 'B. xxxx'.
        it ignores 'A. yyyy' followed by '2.4.1'.
        so it is generous for digit but not so for alphabet header.
        """
        # set generous init value for digit so that the next digit is easy to pass the ordering test
        digits_init: list[str] = ["0", "0", "0"]
        # set strict init value for alphabet so that the next alphabet never passes the ordering test
        abc_init: str = "{"
        digits_last: list[str] = digits_init
        abc_last: str = abc_init
        rows: list[int] = []
        for line in self.lines:
            header: str = line.get_words_at(at_n_th=0)
            header_type = self._get_header_type(header)
            if header_type == self.Header.DIGIT:
                # this looks like ['1','13','5']
                digits_cur: list[str] = self._get_digit_header(header)
                if not self._digits_in_this_order(digits_last, digits_cur):
                    rows.append(line.idx)
                # record the latest digits
                digits_last = digits_cur
                # init back
                abc_last = abc_init
            elif header_type == self.Header.ALPHABET:
                abc_cur: str = self._get_abc_header(header)
                if not self._abc_in_this_order(abc_last, abc_cur):
                    rows.append(line.idx)
                abc_last = abc_cur
                # not init digit
            else:
                rows.append(line.idx)
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

    def get_order_disturbing_main_pages(self) -> Text_Lines:
        """get lines like page-indexed (10,8,13) or (10,14,11)"""
        page_numbers: list[int] = []
        for line in self.lines:
            if not self.has_page_number(line):
                page_numbers.append(-1)
            elif self.is_front_matter(line):
                page_numbers.append(0)
            else:
                page_numbers.append(int(self.get_page_number(line)))
        # run through page numbers list to find disturbing page
        # pick three adjacent elements to check their order consistency
        # ignore 0 since we are not interested in front matter page
        ill_page: list[Text_Line] = []
        L: Final = len(page_numbers)
        INF: Final = (L + 1000) * 10
        for i in range(0, L):
            cur: int = page_numbers[i]
            pre: int = page_numbers[i - 1] if i > 0 else 0
            suc: int = page_numbers[i + 1] if i < L - 1 else INF
            if not self.__is_well_ordered(pre, cur, suc):
                ill_page.append(self.lines[i])
        return Text_Lines(ill_page)

    def get_nearest_page(self, line_ref: Text_Line, search_back: bool = True) -> int:
        """search and get the nearest well-numbered main page number from the reference line. return -1 if nothing found except a front matter page.

        Args:
            line_ref (Text_Line): starting position of the search. this line is not searched.
            search_back (bool, optional): search direction. going back or going ahead. Defaults to True.

        Returns:
            int: the first found page number. -1 if nothing found except a front matter page.
        """
        # the position of the line as a list element in self.lines
        row_idx_ref: int = self.lines.search(row_idx=line_ref.idx)
        L: int = len(self.lines)
        if row_idx_ref < 0:
            raise ValueError("line_ref is not in self.lines.")
        if not search_back and row_idx_ref >= L:
            return -1
        # appropriate starting point of the search, depending on search_back
        start: int = min(row_idx_ref, L) if search_back else row_idx_ref + 1
        for line in reversed(self.lines[:start]) if search_back else self.lines[start:]:
            if self.has_page_number(line) and not self.is_front_matter(line):
                return int(self.get_page_number(line))
        return -1
