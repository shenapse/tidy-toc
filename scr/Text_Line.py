from __future__ import annotations

import re
from enum import IntEnum, auto
from re import Match, Pattern
from typing import Final, Iterator, Optional, overload

from rich import print
from textblob import Word  # type: ignore
from typing_extensions import Self


class Text_Line:
    def __init__(self, idx: int = -1, text: str = "", sep: str = " ") -> None:
        text_slim: str = self.slim_down(text)
        self._validate_text(text_slim)
        self.idx: int = idx
        self._text: str = text_slim
        self._words: list[str] = []
        self._sep: str = sep
        # update words should be manually called in a subclass
        if isinstance(self, Text_Line):
            self.update_words()

    def __lt__(self, other: Self) -> bool:
        return self.idx < other.idx

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: idx={self.idx}, text={self.to_text()}"

    @overload
    def __getitem__(self, key: int) -> str:
        ...

    @overload
    def __getitem__(self, key: slice) -> list[str]:
        ...

    def __getitem__(self, key: int | slice) -> str | list[str]:
        got: str | list[str] = self.words.__getitem__(key)
        return got if isinstance(got, list) else got

    @overload
    def __setitem__(self, key: int, value: str) -> tuple[bool, int | slice]:
        ...

    @overload
    def __setitem__(self, key: slice, value: list[str]) -> tuple[bool, int | slice]:
        ...

    def __setitem__(self, key: int | slice, value: str | list[str]) -> tuple[bool, int | slice]:
        """setter for word in self.words. return true if any elements have been actually altered."""
        # check input
        if isinstance(key, slice) and all(self._validate_text(v) for v in value) and self[key] != value:
            self._words[key] = value
            self._words = self._split()
        elif isinstance(key, int) and isinstance(value, str) and self._validate_text(value) and value != self[key]:
            if value == "":
                self._words.pop(key)
            else:
                self._words[key] = value
        else:  # if neither is true, nothing changed
            return False, key
        # reaching here means something has changed
        self.update_text()
        return True, key

    def __iter__(self) -> Iterator[str]:
        return self._words.__iter__()

    @property
    def sep(self) -> str:
        return self._sep

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, text: str) -> None:
        self._text = text
        self.update_words()

    @property
    def words(self) -> list[str]:
        return self._words

    @words.setter
    def words(self, words: list[str]) -> None:
        self._words = words
        self.update_text()

    def is_empty(self) -> bool:
        return self.to_text() == ""

    def alter_sep(self, sep: str) -> None:
        self._sep = sep

    def to_text(self) -> str:
        return self.text

    def get_instance(self, idx: int, text: str, sep: str) -> Self:
        return Text_Line(idx=idx, text=text, sep=sep)

    def print(self) -> None:
        print(self.to_text())

    def _split(self) -> list[str]:
        return [w.strip() for w in self.text.split(sep=self.sep) if w != ""]

    def update_words(self) -> None:
        self._words = self._split()

    def update_text(self) -> None:
        self._text = self.sep.join(self._words)

    def slim_down(self, text: str = "") -> str:
        """remove leading and trailing spaces and newline."""
        return text.strip()

    def format_space(self) -> Self:
        return self.get_instance(
            idx=self.idx, text=" ".join([t for t in self.to_text().split(" ") if t != ""]), sep=self.sep
        )

    def _has_newline(self, text: str) -> bool:
        return len(lines := text.splitlines()) != 0 and lines[0] != text

    def _validate_text(self, text: str) -> bool:
        """text should be free of newline characters"""
        if self._has_newline(text):
            raise ValueError(f"text must admit no newline character. text={text}")
        return True

    def lookup_word(self, pos_character: int) -> tuple[int, str]:
        """get the word and its positional index (in the list of words) that has the input character position (in the positional index in plain text).
        if input position points a separator character, the word just after the separator is returned.
        e.g., if self.text='hello world' and input=6, then 0, then 'world' is returned."""
        text: str = self.to_text()
        if pos_character < 0 or pos_character > len(text):
            raise IndexError(f"asked position={pos_character} looks at nowhere in '{text}' of length {len(text)}")
        texts: list[str] = text.split(self.sep)
        csum: int = 0
        for i, t in enumerate(texts):
            csum += len(t)
            if csum >= pos_character:
                return i, t
            csum += len(self.sep)
        # this should not be reached
        return len(texts) - 1, texts[-1]

    def get_number_of_words(self) -> int:
        return len(self._words)

    def test_pattern_at(self, pat: Pattern, at: Optional[int] = None) -> bool:
        """test if 'at'-th word has the pat pattern. if 'at' is None, the default, the whole text is tested."""
        target: str = self.text if at is None else self[at]
        return re.search(pat, target) is not None


class Paged_Text_Line(Text_Line):
    page_key: Final[str] = "page"
    roman_page_key: Final[str] = "roman_page"
    pat_page: Final[Pattern] = re.compile(f"(?P<{page_key}>\\s?[0-9]+)$")
    pat_roman_page: Final[Pattern] = re.compile(f"(?=\\s|^)\\s?(?P<{roman_page_key}>[ixv]+|[IXV]+)$")
    pat_word_header: Final[Pattern] = re.compile("^[a-zA-Z]+[\\.,]*$")

    class Header(IntEnum):
        DIGIT = auto()
        ALPHABET = auto()
        WORD = auto()
        NO = auto()

    def __init__(
        self,
        idx: int = -1,
        text: str = "",
        sep: str = " ",
        page_number: Optional[int] = None,
        roman_page_number: Optional[str] = None,
        text_line: Optional[Text_Line] = None,
    ) -> None:
        # about page number
        super().__init__(idx=idx, text=text, sep=sep)
        if text_line is not None:
            self.idx: int = text_line.idx
            self._text: str = text_line.text
            self._sep: str = text_line.sep
        # init page number property
        self.page_number: Optional[int] = page_number
        self.roman_page_number: Optional[str] = roman_page_number
        # automatically separate page number and text
        self.page_number = self._get_page_number() if page_number is None else page_number
        self.roman_page_number = self._get_roman_page_number() if not self.is_page_set() else roman_page_number
        self.header: Paged_Text_Line.Header = self._get_header_type()
        self._text = self._get_text_without_page()
        if isinstance(self, Paged_Text_Line):
            self.update_words()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: idx={self.idx}, text={self.text}, page_number={self.page_number}, roman_page_number={self.roman_page_number}, header_type={self.header.name}"

    def update_page_number(self, overwrite: bool = False) -> None:
        """manually update page number. might be needed if text is significantly changed."""
        if overwrite or not self.is_page_set():
            self.page_number = self._get_page_number()
            self.roman_page_number = self._get_roman_page_number()

    def update_header(self) -> None:
        """manually update header type. might be needed if text is significantly changed."""
        pass

    def get_instance(
        self,
        idx: int = -1,
        text: str = "",
        sep: str = " ",
        page_number: Optional[int] = None,
        roman_page_number: Optional[str] = None,
        text_line: Optional[Text_Line] = None,
    ) -> Self:
        return Paged_Text_Line(
            idx=idx,
            text=text,
            sep=sep,
            page_number=page_number,
            roman_page_number=roman_page_number,
            text_line=text_line,
        )

    def to_text(self, sep: str | None = None, combine: bool = True) -> str:
        """combine text and page number."""
        if not combine or not self.is_page_set():
            return self.text
        separator: str = self.sep if sep is None else sep
        page = self.page_number if self.page_number is not None else self.roman_page_number
        return separator.join([self.text, str(page)])

    def _get_page_number(self) -> int | None:
        """get arabic page number if it exists"""
        match: Optional[Match] = re.search(self.pat_page, self.text)
        return int(match.group(self.page_key)) if match else None

    def get_page_string(self) -> str:
        if self.page_number is not None:
            return str(self.page_number)
        elif self.roman_page_number is not None:
            return self.roman_page_number
        return ""

    def _get_roman_page_number(self) -> str | None:
        """get roman page number. at the time of writing, this method is designed to be called only if no arabic page number is found."""
        match: Optional[Match] = re.search(self.pat_roman_page, self.text)
        return match.group(self.roman_page_key) if match else None

    def is_page_set(self) -> bool:
        """test if page number is set in property, arabic or roman"""
        return self.page_number is not None or self.roman_page_number is not None

    def is_page_number_only(self) -> bool:
        return self.is_page_set() and self.text == ""

    def _get_text_without_page(self) -> str:
        """get text with no page number. this method is assumed to be called only for initiating self.text property in constructor, and not for other purposes."""
        if self.is_page_set():
            is_arabic_page: bool = self.page_number is not None
            pat: Pattern = self.pat_page if is_arabic_page else self.pat_roman_page
            key: str = self.page_key if is_arabic_page else self.roman_page_key
            match: Optional[Match] = re.search(pat, self.text)
            # matches might be empty. it happens, for instance, when page number is directly named in constructor.
            if match:
                text_end: int = match.start(key)
                return self.text[:text_end].strip()
        return self.text

    def _is_valid_word(self, word: str, confidence: float = 1.0) -> bool:
        """test if the input string completely coincides with some word."""
        return re.search(self.pat_word_header, word) is not None and Word(word).spellcheck()[0][1] >= confidence

    def _get_header_type(self) -> Header:
        """judge header type based on the first word on self.text"""
        n_words: int = self.get_number_of_words()
        if (self.is_page_set() and n_words <= 2) or (not self.is_page_set() and n_words <= 1):
            return self.Header.NO
        header: str = self[0]
        if re.search(r"\d+", header):
            return self.Header.DIGIT
        elif self._is_valid_word(header):
            return self.Header.WORD
        elif re.search(r"[a-zA-Z]", header) and len(header) <= 5:
            return self.Header.ALPHABET
        return self.Header.NO
