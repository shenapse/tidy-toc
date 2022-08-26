from typing import Callable, Iterator

import click

from Text_Line import Paged_Text_Line
from Text_Lines import Paged_Text_Lines, Texts_Printer


class Merger:
    def __init__(self, ptls: Paged_Text_Lines) -> None:
        self.lines: Paged_Text_Lines = ptls
        self._printer = Texts_Printer()

    def _merge(self, first: Paged_Text_Line, second: Paged_Text_Line) -> Paged_Text_Line:
        """get the merged paged text line. both texts are combined, the page number is taken from the second, and the other properties are inherited from the first."""
        return Paged_Text_Line(
            idx=first.idx, text=" ".join([first.text, second.text]), sep=first.sep, page_number=second.page_number
        )

    def _ask_whether_merge(self, idx_first: int) -> bool:
        """show candidates lines and ask user if they should be merged."""
        idx_pos: int = self.lines.search(idx_first)
        self._printer.print(
            self.lines, start=idx_pos, end=idx_pos + 1, with_page_idx=False, with_def=False, with_N=False
        )
        return click.prompt(text="merge these rows?", type=bool, default="yes")

    def _map_between(self, fn: Callable[[Paged_Text_Line, Paged_Text_Line], int]) -> Iterator[int]:
        """process each pair of two neighboring elements"""
        itr = iter(self.lines)
        nxt = itr.__next__()
        for x in itr:
            yield fn(nxt, x)
            nxt = x

    def test_pair(self, first: Paged_Text_Line, second: Paged_Text_Line) -> int:
        return (
            first.idx
            if not first.is_page_set()
            and (
                second.is_page_number_only()
                or (
                    second.header != first.Header.DIGIT
                    and first.header != first.Header.NO
                    and not (second.header == first.header and first.header == first.Header.ALPHABET)
                )
            )
            else -1
        )

    def get_candidates(self) -> Paged_Text_Lines:
        """get the first ones of pairs of rows that will be asked to user if they should be merged."""

        def tester(first: Paged_Text_Line, second: Paged_Text_Line) -> int:
            return self.test_pair(first=first, second=second)

        idx: list[int] = [i for i in self._map_between(tester) if i != -1]
        return self.lines.select(idx)

    def get_merged_lines(self) -> Paged_Text_Lines:
        """interactively merge two neighboring lines with page number is missing at the first line and not at the second.
        return the new page text lines output by this process."""
        merged: list[Paged_Text_Line] = []
        idx_to_delete: list[int] = []
        for line in self.get_candidates():
            if self._ask_whether_merge(line.idx):
                line_second: Paged_Text_Line = self.lines.get_line_next_to(line, 1)
                merged.append(self._merge(line, line_second))
                idx_to_delete.append(line_second.idx)
        return self.lines.exclude(idx_to_delete).overwrite(Paged_Text_Lines(merged))
