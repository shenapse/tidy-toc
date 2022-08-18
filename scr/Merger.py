from typing import Callable, Iterator

import click

from Text_Line import Paged_Text_Line
from Text_Lines import Paged_Text_Lines


class Merger:
    def __init__(self, ptls: Paged_Text_Lines) -> None:
        self.lines: Paged_Text_Lines = ptls

    def _merge(self, first: Paged_Text_Line, second: Paged_Text_Line) -> Paged_Text_Line:
        """get the merged paged text line. both texts are combined, the page number is taken from the second, and the other properties are inherited from the first."""
        return Paged_Text_Line(
            idx=first.idx, text=" ".join([first.text, second.text]), sep=first.sep, page_number=second.page_number
        )

    def _ask_whether_merge(self, idx_first: int) -> bool:
        """show candidates lines and ask user if they should be merged."""
        idx_pos: int = self.lines.search(idx_first)
        self.lines[idx_pos].print()
        self.lines[idx_pos + 1].print()
        return click.prompt(text="merge these rows?", type=bool)

    def _map_between(self, fn: Callable[[Paged_Text_Line, Paged_Text_Line], int]) -> Iterator[int]:
        itr = iter(self.lines)
        nxt = itr.__next__()
        for x in itr:
            yield fn(nxt, x)
            nxt = x

    def get_candidates2(self) -> Paged_Text_Lines:
        def test_pair(first: Paged_Text_Line, second: Paged_Text_Line) -> int:
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

        idx: list[int] = [i for i in self._map_between(test_pair) if i != -1]
        return self.lines.select(idx)

    def get_candidates(self) -> Paged_Text_Lines:
        """get the first element of the candidtate pair of lines"""
        end: int = len(self.lines) - 1
        rows: list[int] = [
            line.idx
            for i, line in enumerate(self.lines[:end])
            if not line.is_page_set()
            and (
                self.lines[i + 1].is_page_number_only()
                or (
                    self.lines[i + 1].header != line.Header.DIGIT
                    and line.header != line.Header.NO
                    and not (self.lines[i + 1].header == line.header and line.header == line.Header.ALPHABET)
                )
            )
        ]
        return self.lines.select(rows)

    def get_merged_lines(self) -> Paged_Text_Lines:
        """intercitively merge two neighboring lines with page number is missing at the first line and not at the second.
        retrurn the new page text lines output by this process."""
        merged: list[Paged_Text_Line] = []
        idx_to_delete: list[int] = []
        for line in self.get_candidates2():
            if self._ask_whether_merge(line.idx):
                line_second: Paged_Text_Line = self.lines.get_line_next_to(line, 1)
                merged.append(self._merge(line, line_second))
                idx_to_delete.append(line_second.idx)
        return self.lines.exclude(idx_to_delete).overwrite(Paged_Text_Lines(merged))
