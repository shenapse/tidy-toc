from __future__ import annotations

import abc
import itertools
from typing import Any, Generic, Iterator, Optional, TypeGuard, TypeVar, overload

import rich
from typing_extensions import Self

from Text_Line import Paged_Text_Line, Text_Line

T = TypeVar("T", Text_Line, Paged_Text_Line)


class _Text_Lines(Generic[T], metaclass=abc.ABCMeta):
    """abstract base class for text lines"""

    def __init__(self, texts: list[T] | T) -> None:
        self.lines: list[T] = sorted(texts) if isinstance(texts, list) else [texts]

    def __add__(self, other: Self | list[T]) -> Self:
        """take union of two Text_Lines"""
        return self.get_instance(list(itertools.chain(self, other))).remove_duplication()

    def __sub__(self, other: Self | list[T]) -> Self:
        """self minus other in set difference sense"""
        other_: Self = self.get_instance(other) if isinstance(other, list) else other
        return self.get_instance([s for s in self if not other_.has_row(s.idx)])

    def __and__(self, other: Self | list[T]) -> Self:
        """take intersection of two Text_Lines"""
        other_: Self = self.get_instance(other) if isinstance(other, list) else other
        return self.select(other_.get_index()) if len(self) >= len(other_) else other_.select(self.get_index())

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

    def __len__(self) -> int:
        return len(self.lines)

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

    def is_empty(self) -> bool:
        return len(self) == 0

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

    def overwrite(self, other: Self | list[T]) -> Self:
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

    def get_line(self, row: int) -> T:
        """get Text_Line object with the row number in self"""
        if not self.has_row(row):
            raise ValueError(f"row={row} not found.")
        return self[self.search(row)]

    def get_line_next_to(self, line: T, move: int = 1) -> T:
        """get Text line object in self that is away from input 'line' with just 'move' amount in terms of positional index in list."""
        if not self.has_row(line.idx):
            raise ValueError(f"{self} does not contain {line}.")
        idx: int = self.search(line.idx)
        if not self.has_row_at(line=line, move=move):
            raise IndexError(
                f"{self} of length {len(self)} contains {line} at {idx}, but impossible to make a {move} move from there."
            )
        return self[idx + move]

    def has_row_at(self, line: T, move: int = 1) -> bool:
        """test if self has an element at moved position from where line is placed."""
        return self.has_row(line.idx) != -1 and 0 <= (self.search(line.idx) + move) < len(self)

    def get_rows_around(self, line: T, radius: int) -> Self:
        moves: list[int] = [i for i in range(-abs(radius), abs(radius) + 1) if i != 0]
        return self.get_instance(
            [self.get_line_next_to(line=line, move=move) for move in moves if self.has_row_at(line, move)]
        )

    def get_row_idx(self, idx: int) -> int:
        return self[idx].idx

    def remove_blank_rows(self) -> Self:
        rows: list[int] = [line.idx for line in self if not line.is_empty()]
        return self.select(rows=rows)

    def format_space(self) -> Self:
        return self.get_instance([line.format_space() for line in self])


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


class Texts_Printer:
    def __init__(self, color_set: list[str] = ["magenta", "cyan"]) -> None:
        self._color_set: list[str] = ["magenta", "cyan"] if color_set is None else color_set

    def generate_color_block(self, color: Optional[str] = None) -> tuple[str, str]:
        c = self._color_set[0] if color is None else color
        return f"[{c}]", "[/]"

    def coloring(self, text: str, color: Optional[str] = None) -> str:
        c = self._color_set[0] if color is not None else color
        begin, end = self.generate_color_block(color=c)
        return f"{begin}{text}{end}" if c != "" else text

    def get_colored(self, components: list[str], color_orders: list[tuple[int, str]] = []) -> list[str]:
        # get MECE color orders
        order_eff: list[tuple[int, str]] = [(i, c) for i, c in color_orders if i in range(len(components))]
        idx_eff: set[int] = set()
        order_mece: list[tuple[int, str]] = []
        for i, c in order_eff:
            if i not in idx_eff:
                order_mece.append((i, c))
            idx_eff.add(i)
        for i in range(len(components)):
            if i not in idx_eff:
                order_mece.append((i, ""))
        order_mece.sort()
        return [self.coloring(components[pos], color) for (pos, color) in order_mece]

    Lines = TypeVar("Lines", Text_Lines, Paged_Text_Lines)

    def print(
        self,
        lines: Lines,
        start: int = 0,
        end: int = -1,
        with_N: bool = True,
        with_page_idx: bool = True,
        with_def: bool = True,
        colors: list[tuple[int, str]] = [],
        with_blank_line: bool = True,
    ) -> None:
        """print continuous part of text lines.
        By default it prints all lines."""

        colors = colors if colors != [] else [(0, self._color_set[0]), (1, self._color_set[-1])]
        sep: str = " | "

        def filter_texts(texts: list[str]) -> list[str]:
            """pick appropriate elements based on with_** conditions, assuming that input list comes with the form [N, idx, text]"""
            if with_N and with_page_idx:
                return texts
            elif not with_N and not with_page_idx:
                return [texts[-1]]
            return [texts[0], texts[-1]] if with_N else [texts[1], texts[-1]]

        if with_blank_line:
            self.insert_blank_line()

        # create and print def header if necessary
        if with_def:
            elems: list[str] = ["N", "Row", "Text"]
            colored_elems: list[str] = self.get_colored(elems, colors)
            rich.print(sep.join(filter_texts(colored_elems)))

        # print main part
        end_: int = min(end + 1, len(lines)) if end > 0 else len(lines)
        for i in range(max(start, 0), end_):
            elems: list[str] = [f"{i-start}", f"{lines[i].idx}", f"{lines[i].to_text()}"]
            rich.print(sep.join(filter_texts(elems)))

        if with_blank_line:
            self.insert_blank_line()

    def print_around(
        self,
        lines: Lines,
        row: int,
        N_around: int = 1,
        coloring_at: list[int] = [0],
        coloring_with: Optional[str] = None,
        with_blank_line: bool = True,
    ) -> None:
        color: str = self._color_set[0] if coloring_with is None else coloring_with
        i_center: int = lines.search(row)
        if i_center == -1:
            return
        include: list[int] = [
            i + i_center for i in range(-N_around, N_around + 1) if i + i_center in range(0, len(lines))
        ]
        color_pos: list[int] = [i + i_center for i in coloring_at if i + i_center in include]
        if with_blank_line:
            self.insert_blank_line()
        for i in include:
            out: str = self.coloring(lines[i].to_text(), color) if i in color_pos else lines[i].to_text()
            rich.print(out)
        if with_blank_line:
            self.insert_blank_line()

    def insert_blank_line(self) -> None:
        print("")
