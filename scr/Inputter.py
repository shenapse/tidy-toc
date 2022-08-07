from __future__ import annotations

import abc
import re
from enum import IntEnum, auto
from re import Match, Pattern
from typing import Callable, Final, Iterable

import click
from rich import print


class Input_lines:
    def __init__(self) -> None:
        self.input: list[int] = []

    def get_input(self) -> list[int]:
        return self.input

    def __validate_input(self, x: list[int], range: list[int]) -> bool:
        if any(abs(v) not in range for v in x):
            raise ValueError(f"too big input. maximum value for this line is {range}")
        return True

    def __first_lowered_term(self, data: str) -> str:
        return data.lower().split(sep=" ")[0]

    def __has_none_phrase(self, data: str) -> bool:
        return self.__first_lowered_term(data) in ["no", "n", "none"]

    def __has_all_phrase(self, data: str) -> bool:
        return self.__first_lowered_term(data) in ["a", "all"]

    def __has_minus_zero(self, data: str) -> bool:
        return "-0" in data.split(" ")

    def prompt(
        self,
        range: list[int],
        msg: str = "",
        sep: str = " ",
    ) -> None:
        """ask input by prompt until proper value is set.
        if input ...

        - is a or all: select all of range

        - are positive integers(separated by single space): int list of them

        - contains negative integer(s): select all of range except the integer(s)
        """
        while True:
            inp: str = click.prompt(msg, type=str)
            try:
                # detect keywords. ask input again if all of them fail
                if self.__has_none_phrase(inp):
                    self.input = []
                    break
                elif self.__has_all_phrase(inp):
                    self.input = range
                    break
                casted: list[int] = [int(s) for s in inp.split(sep)]
                if self.__validate_input(casted, range):
                    # negative integer dominates positive integer
                    with_minus_zero = self.__has_minus_zero(inp)
                    seq: list[int] = (
                        self.__reverse_negative(casted, range, with_minus_zero)
                        if self.__has_negative(casted, with_minus_zero)
                        else casted
                    )
                    self.input = self.__filter_input(seq)
                    break
            except ValueError:
                print("invalid input. non-integer or too large.")
                continue
            else:
                raise Exception("Invalid input causes an unexpected error.")

    def __has_negative(self, data: list[int], with_minus_zero: bool) -> bool:
        return with_minus_zero or any(x < 0 for x in data)

    def __reverse_negative(self, data: list[int], range: list[int], with_minus_zero: bool) -> list[int]:
        """deal with negative integer input"""
        list_neg: list[int] = [0] if with_minus_zero else []
        list_neg.extend([abs(x) for x in data if x < 0])
        return [x for x in range if x not in list_neg]

    def __filter_input(self, data: list[int]) -> list[int]:
        """remove duplicating elements in the list and return it as a sorted one."""
        ret: list[int] = []
        for x in data:
            if x not in ret:
                ret.append(x)
        return sorted(ret)


class _Input(metaclass=abc.ABCMeta):
    @abc.abstractclassmethod
    def prompt(self, msg: str = "") -> None:
        raise NotImplementedError

    @abc.abstractclassmethod
    def get_input(self) -> list[int]:
        raise NotImplementedError


class Inputter(_Input):
    class Word(str):
        """restriction of str class to \\S and lower case."""

        pat: Final[Pattern] = re.compile("^\\S+$")

        def __new__(cls, val: str):
            self = super().__new__(cls, val.lower())
            self.validate_text(val)
            return self

        def validate_text(self, text: str) -> bool:
            if list(re.finditer(self.pat, text)) == []:
                raise ValueError(f"Invalid input. {text} contains a forbidden character.")
            return True

    class Sentence(str):
        """restriction of str class to [\\S ] and lower case."""

        pat: Final[Pattern] = re.compile("^[\\S ]+$")

        def __new__(cls, val: str):
            self = super().__new__(cls, val.lower())
            self.validate_text(val)
            return self

        def validate_text(self, text: str) -> bool:
            if list(re.finditer(self.pat, text)) == []:
                raise ValueError(f"Invalid input. {text} contains a forbidden character.")
            return True

        def to_words(self) -> list[Inputter.Word]:
            return [Inputter.Word(s) for s in self.split()]

    # regexp patterns and their key names
    class Digit:
        """dataclass that holds Pattern object for detecting digit pattern and key to get detected digit."""

        calls: Final[list[str]] = ["digit"]
        pat: Final[Pattern] = re.compile(f"^(?!-)(?P<{calls[0]}>\\d+)(?<!-)$")

    class Minus:
        calls: Final[list[str]] = ["minus"]
        pat: Final[Pattern] = re.compile(f"^(?<!\\d)-(?P<{calls[0]}>\\d+)$")

    class Range:
        calls: Final[list[str]] = ["first", "second"]
        pat: Final[Pattern] = re.compile(f"(?P<{calls[0]}>^\\d+)-(?P<{calls[1]}>\\d+)$")

    class Phrase:
        """holds identifiers key phrases as Phrase.Name and corresponding Pattern objects that detect the phrases in raw input"""

        class Pat:
            none_raw: Final[str] = "^n$|^no$|^none$"
            none: Final[Pattern] = re.compile(none_raw)
            all_raw: Final[str] = "^a$|^all$"
            all: Final[Pattern] = re.compile(all_raw)
            help_raw: Final[str] = "^h$|^help$"
            help: Final[Pattern] = re.compile(help_raw)

        class Name(IntEnum):
            NONE = auto()
            ALL = auto()
            HELP = auto()  # set as dominant by is_dominant()

        @classmethod
        def get_pattern(cls, name: Name) -> Pattern:
            """get the Pattern object that corresponds to Phrase.Name member"""
            match name:
                case cls.Name.NONE:
                    return cls.Pat.none
                case cls.Name.ALL:
                    return cls.Pat.all
                case cls.Name.HELP:
                    return cls.Pat.help
                case _:
                    raise ValueError(f"{name} does not match any of {cls.__name__}.{cls.Name.__name__}.")

        @classmethod
        def is_dominant(cls, name: Name) -> bool:
            """provides DEFINITION of dominant names and tester of them."""
            if name not in cls.Name:
                raise ValueError(f"{name} is not in {cls.Name.__name__}.")
            return name == cls.Name.HELP

        @classmethod
        def get_dominant_names(cls) -> list[Name]:
            """get dominant names in Phrase class. Note that dominant names are not defined explicitly in their propertry, but implicitly by is_dominant_function."""
            return [name for name in cls.Name if cls.is_dominant(name)]

    def __init__(self, max_line: int = 10) -> None:
        if max_line <= 0 or not isinstance(max_line, int):
            raise ValueError("max line must be a postive integer.")
        self.__max_line: int = max_line
        self.__range: set[int] = set(range(0, max_line + 1))
        self.__input: set[int] = set()
        self.__valid_words: set[Inputter.Word] = self.list_valid_words()

    @property
    def input(self) -> set[int]:
        """get current input as a set."""
        return self.__input

    @property
    def max_line(self) -> int:
        return self.__max_line

    @property
    def range(self) -> set[int]:
        return self.__range

    @property
    def valid_words(self) -> set[Word]:
        return self.__valid_words

    def clear(self) -> None:
        """Initialize self.__input while self.max_line and self.range remain kept."""
        self.__input.clear()

    def get_input(self) -> list[int]:
        """get the translated input. The output list is sorted and admits no duplicated elements."""
        return list(self.input)

    def _is_in_range(self, x: int | set[int]) -> bool:
        """test if the input integer or set of interges is in valid range determined by max_line."""
        return x in self.range if isinstance(x, int) else x.issubset(self.range)

    def _get_matches(self, pat: Pattern, word: str) -> list[Match]:
        """get the list of re.Match objects that correspond to input pattern and word."""
        return list(re.finditer(pat, word))

    def _test_match(self, pat: Pattern, word: Word) -> bool:
        """test if the input pair of pattern and word hits something nonempty."""
        return self._get_matches(pat, word) != []

    def _test_match_by(self, pats: list[Pattern], word: Word, eval: Callable[[Iterable], bool] = any) -> bool:
        """An extention of _test_match() to accept many patterns. returns the result processed by the eval function."""
        return eval(self._test_match(pat, word) for pat in pats)

    def _apply_digit_pattern(self, word: Word) -> None:
        """add digit to input property specified by word, assuming word corresponds to a digit pattern."""
        self.__input.add(self._get_matched_integers(self.Digit(), word)[0])

    def _apply_minus_pattern(self, word: Word) -> None:
        """minus digit from input property specified by word, assuming word corresponds to a minus digit pattern."""
        self.__input.discard(self._get_matched_integers(self.Minus(), word)[0])

    def _apply_range_pattern(self, word: Word) -> None:
        """add digits to input property specified by word, assuming word corresponds to a range pattern."""
        x, y = self._get_matched_integers(self.Range(), word)
        self.__input = self.input | set(range(min(x, y), max(x, y) + 1))

    def _get_matched_integers(
        self, match_cls: Inputter.Digit | Inputter.Minus | Inputter.Range, word: Word
    ) -> list[int]:
        """get list of integers when the pair of pattern (of match_cls) and word hits something meaningful."""
        return [int(self._get_matches(match_cls.pat, word)[0].group(call)) for call in match_cls.calls]

    def _get_matched_phrase(self, word: Word) -> Phrase.Name:
        """get the first phrase hit in word. Error if it hits no phrases."""
        for name in self.Phrase.Name:
            if self._test_match(self.Phrase.get_pattern(name), word):
                return name
        raise Exception(f"{word} does not match any of {self.Phrase.__name__}.")

    def _apply_phrase(self, word: Word) -> None:
        """to input, apply in-place change meant by phrase in word. an error wil be raised if word is not a phrase."""
        match self._get_matched_phrase(word):  # raise error if it is not a phrase
            case self.Phrase.Name.ALL:
                self.__input = self.range
            case self.Phrase.Name.NONE:
                self.clear()

    def _exist_dominant_phrase(self, word: Word) -> bool:
        """test if word has a dominant phrase."""
        return any(
            self._test_match(self.Phrase.get_pattern(d_name), word) for d_name in self.Phrase.get_dominant_names()
        )

    def _find_dominant_phrase(self, word: Word) -> Phrase.Name:
        """get the most dominant phrase in word."""
        d_phrases = [
            name for name in self.Phrase.get_dominant_names() if self._test_match(self.Phrase.get_pattern(name), word)
        ]
        if len(d_phrases) > 1:
            raise Exception(f"Multiple dominant phrases are found in {word}. It must be at most one.")
        elif len(d_phrases) == 0:
            raise ValueError(f"No dominant phrase are found in {word}")
        return d_phrases[0]

    def print_help(self) -> None:
        """show help typically triggered by help phrase."""
        print("help!")

    def list_valid_words(self) -> set[Word]:
        """get the possible charasters for input. It is defiend as the set {numrical characters in range} | {space and -} | {characters in phrase}."""
        # default set consists of numerical characters and space and -.
        default: set[Inputter.Word] = {self.Word(" "), self.Word("\\-")}.union(
            [self.Word(str(r)) for r in range(0, 10)]
        )
        # characters in phrase
        pat: Pattern = re.compile("[a-z]")
        src: str = self.Phrase.Pat.all_raw + self.Phrase.Pat.none_raw + self.Phrase.Pat.help_raw
        matches: list[Match] = list(re.finditer(pat, src))
        return set([self.Word(m.group(0)) for m in matches]).union(default)

    def _check_length(self, sentence: Sentence) -> bool:
        return len(sentence) <= self.max_line * 5

    def _check_words(self, sentence: Sentence) -> bool:
        pat: Pattern = re.compile("[^" + "".join(self.valid_words) + "]")
        return list(re.finditer(pat, sentence)) == []

    def ask(self, msg: str = "") -> None:
        pass

    def prompt(self, msg: str = "") -> None:
        """ask user to type input in CLI repeatedly until it gets a valid one."""
        pass
