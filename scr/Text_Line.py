from __future__ import annotations

import itertools
from typing import Any, TypeGuard

from rich import print


class Text_Line:
    def __init__(self, idx: int = -1, text: str = "") -> None:
        self.idx: int = idx
        self.text: str = text

    def __lt__(self, other: Text_Line) -> bool:
        return self.idx < other.idx

    def __iter__(self):
        return self

    def __repr__(self) -> str:
        return f"Text_Line: idx={self.idx}, text={self.text}"

    def is_empty(self) -> bool:
        return self.idx == -1 or self.text == ""

    def print(self) -> None:
        print(self.text)


class Text_Lines(list[Text_Line]):
    def __init__(self, text: str | list[str] | list[Text_Line] = ""):
        if text != "":
            if isinstance(text, str):
                # if plain text, split and construct list[Text_Line]
                super().__init__(self.__get_pre_Text_Lines(text))
            elif self.__is_list_Text_Line(text):
                super().__init__(text)
                self.sort()
            elif self.__is_list_str(text):
                super().__init__(self.__get_pre_Text_Lines(text))
            else:
                raise Exception(f"invalid type: text = {type(text)}")
        else:
            super().__init__()

    def __add__(self, other: Text_Lines) -> Text_Lines:
        """take union of two Text_Lines"""
        return Text_Lines(list(itertools.chain(self, other))).remove_duplication().get_sorted()

    def __sub__(self, other: Text_Lines) -> Text_Lines:
        """self minus other in set difference sense"""
        return Text_Lines([s for s in self if not other.has_row(s.idx)])

    def __and__(self, other: Text_Lines) -> Text_Lines:
        """take intersection of two Text_Lines"""
        return self.select(other.get_index()) if len(self) >= len(other) else other.select(self.get_index())

    def __repr__(self) -> str:
        n_show: int = 10
        return "\n".join(["Text_Lines starts with"] + [s.__repr__() for s in self[:n_show]])

    def __is_list_Text_Line(self, text: Any) -> TypeGuard[list[Text_Line]]:
        return isinstance(text, list) and (True if len(text) == 0 else isinstance(text[0], Text_Line))

    def __is_list_str(self, text: Any) -> TypeGuard[list[str]]:
        return isinstance(text, list) and (True if len(text) == 0 else isinstance(text[0], str))

    def __get_pre_Text_Lines(self, text: str | list[str]) -> list[Text_Line]:
        texts: list[str] = text.splitlines() if isinstance(text, str) else text
        return [Text_Line(i, s) for i, s in enumerate(texts)]

    def is_empty(self) -> bool:
        return len(self) == 0

    def print(self, start: int = 0, end: int = -1, with_header=True):
        """print continuous part of text lines.
        By default it prints all lines."""
        end_: int = end if end > 0 else len(self)
        if with_header:
            print("[magenta]N[/] : [cyan]Row[/] : Text")
        for i in range(start, end_):
            print(f"[magenta]{i-start}[/] : {self[i].idx} : {self[i].text}")

    def print_around(self, at: int, offset: int = 2):
        at_: int = min(at, len(self) - 1)
        start: int = max(0, at_ - offset)
        end: int = min(at_ + offset, len(self) - 1)
        for i in range(start, end + 1):
            if i == at_:
                print(f"[bold magenta]{self[i].text}[/]")
            else:
                print(f"{self[i].text}")

    def get_index(self) -> list[int]:
        return [s.idx for s in self]

    def to_list_str(self) -> list[str]:
        return [s.text for s in self]

    def to_text(self) -> str:
        return "\n".join(self.to_list_str())

    def __to_sorted_unique(self, x: list[int]) -> list[int]:
        ret: list[int] = []
        for v in sorted(x):
            if ret == [] or v != ret[-1]:
                ret.append(v)
        return ret

    def select(self, rows: list[int]) -> Text_Lines:
        """filter self into Text_Lines whose row numbers in rows input."""
        if rows == []:
            return Text_Lines()
        return Text_Lines([self.get_line(i) for i in self.__to_sorted_unique(rows) if self.has_row(i)])

    def exclude(self, rows: list[int]) -> Text_Lines:
        return self - self.select(rows)

    # def filter(self, cdn: list[int] | Text_Lines = [], exclude: bool = True) -> Text_Lines:
    #     """get a new text lines object without input cdn lines"""
    #     if len(cdn) == 0:
    #         return self if exclude else Text_Lines()
    #     index: list[int] = cdn.get_index() if isinstance(cdn, Text_Lines) else cdn
    #     return (
    #         Text_Lines([s for s in self if s.idx not in index])
    #         if exclude
    #         else Text_Lines([s for s in self if s.idx in index])
    #     )

    def remove_duplication(self) -> Text_Lines:
        """remove duplicated lines and return the removed lines."""
        idx_unique: list[int] = self.__to_sorted_unique(self.get_index())
        return self.select(idx_unique)

    def get_sorted(self) -> Text_Lines:
        self.sort()
        return self

    def search(self, row_idx: int, left: int = 0, right: int = -1) -> int:
        """binary search Text_Line in self with the asked row. Return the index if found and -1 if not."""
        N: int = len(self)
        le: int = left
        r: int = N - 1 if right == -1 else min(right, N)
        while le <= r:
            center = (r + le) // 2
            if self[center].idx == row_idx:
                return center
            elif self[center].idx < row_idx:
                le = center + 1
            else:
                r = center - 1
        return -1

    def has_row(self, row: int) -> bool:
        """if Text_Lines object has the asked row"""
        return self.search(row) != -1

    def get_line(self, row: int) -> Text_Line:
        """get Text_Line object with the row number in self"""
        if not self.has_row(row):
            raise ValueError(f"row={row} not found.")
        return self[self.search(row)]

    def get_row_idx(self, idx: int) -> int:
        return self[idx].idx
