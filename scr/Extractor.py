from __future__ import annotations

import re
from typing import Final

from Text_Line import Text_Line, Text_Lines


class Extractor:
    def __init__(self, text: list[str] | str | Text_Lines = []) -> None:
        # lines of text edit
        if isinstance(text, Text_Lines):
            self.lines: Text_Lines = text
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

    def is_front_matter(self, line: Text_Line) -> bool:
        """
        yes if line has a page number like iii or iv or xii.
        no if 1 or 50 or 100.
        error if otherwise
        """
        if not self.has_page_number(line):
            raise Exception("No page number found.")
        return re.findall(r"\s[ixv]+$|\s[IXV]+$", line.text) != []

    def get_non_numbered_pages(self) -> Text_Lines:
        return Text_Lines([line for line in self.lines if not self.has_page_number(line)])

    def get_unexpected_front_matter_pages(self) -> Text_Lines:
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
        return Text_Lines(self.lines).select(ill_idx)

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

    def get_ill_ordered_pages(self) -> Text_Lines:
        """get lines that disturb page order."""
        return Text_Lines(
            (self.get_non_numbered_pages() + self.get_unexpected_front_matter_pages()).get_sorted()
        ).remove_duplication()

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


if __name__ == "__main__":
    with open("../sample/MCSM.txt") as f:
        text = f.read()
