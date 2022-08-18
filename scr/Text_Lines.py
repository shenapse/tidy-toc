from __future__ import annotations

import abc
import itertools
from typing import Any, Generic, Iterator, TypeGuard, TypeVar, overload

from rich import print
from typing_extensions import Self

from Text_Line import Paged_Text_Line, Text_Line

T = TypeVar("T", Text_Line, Paged_Text_Line)


class _Text_Lines(Generic[T], metaclass=abc.ABCMeta):
    """abstract base class for text lines"""

    def __init__(self, texts: list[T] | T) -> None:
        self.lines: list[T] = sorted(texts) if isinstance(texts, list) else [texts]

    def __add__(self, other: Self) -> Self:
        """take union of two Text_Lines"""
        return self.get_instance(list(itertools.chain(self, other))).remove_duplication().get_sorted()

    def __sub__(self, other: Self) -> Self:
        """self minus other in set difference sense"""
        return self.get_instance([s for s in self if not other.has_row(s.idx)])

    def __and__(self, other: Self) -> Self:
        """take intersection of two Text_Lines"""
        return self.select(other.get_index()) if self.len() >= other.len() else other.select(self.get_index())

    @overload
    def __getitem__(self, key: int) -> T:
        ...

    @overload
    def __getitem__(self, key: slice) -> Self:
        ...

    def __getitem__(self, key: int | slice) -> Self | T:
        value: list[T] | T = self.lines.__getitem__(key)
        return self.get_instance(value) if isinstance(value, list) else value

    def __iter__(self) -> Iterator[T]:
        return self.lines.__iter__()

    def __repr__(self) -> str:
        n_show: int = 10
        return "\n".join([f"{self.__class__.__name__} starts with"] + [s.__repr__() for s in self[:n_show]])

    def _is_list_T(self, text: Any) -> TypeGuard[list[T]]:
        return isinstance(text, list) and (len(text) == 0 or isinstance(text[0], (Text_Line, Paged_Text_Line)))

    def _is_list_str(self, text: Any) -> TypeGuard[list[str]]:
        return isinstance(text, list) and (True if len(text) == 0 else isinstance(text[0], str))

    @abc.abstractmethod
    def _to_list_T(self, text: str | list[str]) -> list[T]:
        # texts: list[str] = text.splitlines() if isinstance(text, str) else text
        raise NotImplementedError

    @abc.abstractmethod
    def get_instance(self, texts: list[T] | T) -> Self:
        raise NotImplementedError

    def len(self) -> int:
        return len(self.lines)

    def is_empty(self) -> bool:
        return self.len() == 0

    def is_nonempty(self) -> TypeGuard[Self]:
        return not self.is_empty()

    def get_index(self) -> list[int]:
        return [s.idx for s in self]

    def to_list_str(self) -> list[str]:
        return [s.to_text() for s in self]

    def to_text(self) -> str:
        return "\n".join(self.to_list_str())

    def __to_sorted_unique(self, x: list[int]) -> list[int]:
        ret: list[int] = []
        for v in sorted(x):
            if ret == [] or v != ret[-1]:
                ret.append(v)
        return ret

    def select(self, rows: list[int]) -> Self:
        """filter self into Self whose row numbers are in rows input."""
        return self.get_instance([self.get_line(i) for i in self.__to_sorted_unique(rows) if self.has_row(i)])

    def exclude(self, rows: list[int]) -> Self:
        """filter out self to Self whose rows numbers are not in rows input."""
        return self - self.select(rows)

    def overwrite(self, other: Self) -> Self:
        return (self - other) + other

    def remove_duplication(self) -> Self:
        """remove duplicated lines and return the removed lines."""
        idx_unique: list[int] = self.__to_sorted_unique(self.get_index())
        return self.select(idx_unique)

    def get_sorted(self) -> Self:
        self.lines.sort()
        return self

    def search(self, row_idx: int, left: int = 0, right: int = -1) -> int:
        """binary search the positional index of self with the asked row. Return the index if found and -1 if not."""
        N: int = self.len()
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

    def get_line(self, row: int) -> T:
        """get Text_Line object with the row number in self"""
        if not self.has_row(row):
            raise ValueError(f"row={row} not found.")
        return self[self.search(row)]

    def get_line_next_to(self, line: T, move: int = 1) -> T:
        """get Text line object in self that is away from input 'line' with just 'move' amount in terms of positional index in list."""
        if not self.has_row(line.idx):
            raise ValueError(f"{self} does not contain {line}.")
        if not 0 <= (idx_pos := self.search(line.idx) + move) < self.len():
            raise IndexError(
                f"{self} of length {self.len()} contains {line} at {idx_pos-move}, but impossible to make a {move} move from there."
            )
        return self[idx_pos]

    def get_row_idx(self, idx: int) -> int:
        return self[idx].idx

    def remove_blank_rows(self) -> Self:
        rows: list[int] = [line.idx for line in self if not line.is_empty()]
        return self.select(rows=rows)

    def format_space(self) -> Self:
        return self.get_instance([line.format_space() for line in self])

    def print(
        self,
        start: int = 0,
        end: int = -1,
        with_page_idx: bool = True,
        with_header: bool = True,
    ) -> None:
        """print continuous part of text lines.
        By default it prints all lines."""
        end_: int = end if end > 0 else self.len()
        if with_header:
            header_elems: list[str] = ["[magenta]N[/]", page_idx := "[cyan]Row[/]", "Text"]
            if not with_page_idx:
                header_elems.remove(page_idx)
            header: str = " | ".join(header_elems)
            print(header)
        for i in range(start, end_):
            print_elems: list[str] = [
                f"[magenta]{i-start}[/]",
                page_idx := f"{self[i].idx}",
                f"{self[i].to_text()}",
            ]
            if not with_page_idx:
                print_elems.remove(page_idx)
            print(" | ".join(print_elems))


class Text_Lines(_Text_Lines[Text_Line]):
    def __init__(self, text: str | list[str] | list[Text_Line] = "") -> None:
        if self._is_list_str(text) or isinstance(text, str):
            super().__init__(self._to_list_T(text))
        elif self._is_list_T(text):
            super().__init__(text)
        else:
            raise TypeError(f"invalid type: text = {type(text)}")

    def _to_list_T(self, text: str | list[str]) -> list[Text_Line]:
        texts: list[str] = text.splitlines() if isinstance(text, str) else text
        return [Text_Line(i, s) for i, s in enumerate(texts)]

    def get_instance(self, texts: list[Text_Line]) -> Self:
        return Text_Lines(texts)


class Paged_Text_Lines(_Text_Lines[Paged_Text_Line]):
    def __init__(self, text: str | list[str] | list[Paged_Text_Line] = "") -> None:
        if self._is_list_str(text) or isinstance(text, (str)):
            super().__init__(self._to_list_T(text))
        elif self._is_list_T(text):
            super().__init__(text)
        else:
            raise TypeError(f"invalid type: text = {type(text)}")

    def _to_list_T(self, text: str | list[str]) -> list[Paged_Text_Line]:
        # text is str or list[str]
        texts: list[str] = text.splitlines() if isinstance(text, str) else text
        return [Paged_Text_Line(i, s) for i, s in enumerate(texts)]

    def get_instance(self, texts: list[Paged_Text_Line]) -> Self:
        return Paged_Text_Lines(texts)

    def to_list_str(self, combine: bool = True) -> list[str]:
        return [s.to_text(combine=combine) for s in self]

    def to_text(self, combine: bool = True) -> str:
        return "\n".join(self.to_list_str(combine=combine))
