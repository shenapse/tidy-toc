from __future__ import annotations

import itertools
from typing import Any, TypeGuard

from rich import print


class Text_Line:
    def __init__(self, idx: int = -1, text: str = "", sep: str = " ") -> None:
        text_slim: str = self.slim_down(text)
        self._validate_text(text_slim)
        self.idx: int = idx
        self.text: str = text_slim
        self._sep: str = sep

    def __lt__(self, other: Text_Line) -> bool:
        return self.idx < other.idx

    def __iter__(self):
        return self

    def __repr__(self) -> str:
        return f"Text_Line: idx={self.idx}, text={self.text}"

    @property
    def sep(self) -> str:
        return self._sep

    def is_empty(self) -> bool:
        return self.text == ""

    def alter_sep(self, sep: str) -> None:
        self._sep = sep

    def print(self) -> None:
        print(self.text)

    def slim_down(self, text: str = "") -> str:
        """remove leading and trailing spaces and newline."""
        return text.strip()

    def format_space(self) -> Text_Line:
        return Text_Line(idx=self.idx, text=" ".join([t for t in self.text.split(" ") if t != ""]))

    def _has_newline(self, text: str) -> bool:
        return len(lines := text.splitlines()) != 0 and lines[0] != text

    def _validate_text(self, text: str) -> bool:
        """text should be free of newline characters"""
        if self._has_newline(text):
            raise ValueError(f"text must admit no newline character. text={text}")
        return True

    def get_words_at(self, at_n_th: int, strip: bool = True) -> str:
        pre_strip: str = self.text.split(self.sep)[at_n_th]
        return pre_strip.strip() if strip else pre_strip

    def get_number_of_words(self) -> int:
        return len(self.text.split(self.sep))

    def replace_words_at(self, at_n_th: int, replace_with: str) -> str:
        texts: list[str] = self.text.split(self.sep)
        old: str = texts[at_n_th]
        if replace_with == "":
            popped: str = texts.pop(at_n_th)
            self.text = self.sep.join(texts)
            return popped
        else:
            texts[at_n_th] = replace_with
            self.text = self.sep.join(texts)
            return old


class Text_Lines(list[Text_Line]):
    def __init__(self, text: str | list[str] | list[Text_Line] = ""):
        if self.__is_list_str(text):
            super().__init__(self.__get_pre_Text_Lines(text))
        elif self.__is_list_Text_Line(text):
            super().__init__(text)
            self.sort()
        elif isinstance(text, str):
            # if plain text, split and construct list[Text_Line]
            super().__init__(self.__get_pre_Text_Lines(text))
        else:
            raise Exception(f"invalid type: text = {type(text)}")

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

    def is_nonempty(self) -> TypeGuard[Text_Lines]:
        return len(self) != 0

    def print(self, start: int = 0, end: int = -1, with_page_idx: bool = True, with_header: bool = True):
        """print continuous part of text lines.
        By default it prints all lines."""
        end_: int = end if end > 0 else len(self)
        if with_header:
            header_elems: list[str] = ["[magenta]N[/]", page_idx := "[cyan]Row[/]", "Text"]
            if not with_page_idx:
                header_elems.remove(page_idx)
            header: str = " | ".join(header_elems)
            print(header)
        for i in range(start, end_):
            print_elems: list[str] = [f"[magenta]{i-start}[/]", page_idx := f"{self[i].idx}", f"{self[i].text}"]
            if not with_page_idx:
                print_elems.remove(page_idx)
            print(" | ".join(print_elems))

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
        """filter self into Text_Lines whose row numbers are in rows input."""
        if rows == []:
            return Text_Lines()
        return Text_Lines([self.get_line(i) for i in self.__to_sorted_unique(rows) if self.has_row(i)])

    def exclude(self, rows: list[int]) -> Text_Lines:
        return self - self.select(rows)

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

    def remove_blank_rows(self) -> Text_Lines:
        rows: list[int] = [line.idx for line in self if not line.is_empty()]
        return self.select(rows=rows)

    def format_space(self) -> Text_Lines:
        return Text_Lines([line.format_space() for line in self])
