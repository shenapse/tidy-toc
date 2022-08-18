from __future__ import annotations

import itertools
import re
from enum import IntEnum, auto
from re import Pattern
from typing import Callable, Final, Iterable


class Interpreter:
    class Word(str):
        """restriction of str class to \\S and lower case."""

        pat: Final[Pattern] = re.compile("[^\\S]")

        def __new__(cls, val: str):
            self = super().__new__(cls, val.lower())
            self.validate_text(val)
            return self

        def validate_text(self, text: str) -> bool:
            if text == "":
                raise ValueError(f"{text} is empty.")
            elif (L := re.search(self.pat, text)) is not None:
                raise ValueError(f"Invalid input. {text} contains a forbidden character {L.group()}.")
            return True

    class Sentence(str):
        """restriction of str class to [\\S ] and lower case."""

        pat: Final[Pattern] = re.compile("[^\\S ]")
        pat_ng: Final[Pattern] = re.compile("^\\s+$")

        @classmethod
        def is_sentenceable(cls, text: str) -> bool:
            return text != "" and re.search(cls.pat, text) is None and re.search(cls.pat_ng, text) is None

        @classmethod
        def get_error_msg(cls, text: str) -> str | None:
            if text == "":
                return "empty text."
            elif (L := re.search(cls.pat, text)) is not None:
                return f"Invalid input. {text} contains a forbidden character {L.group()}."
            elif re.search(cls.pat_ng, text) is not None:
                return "text contains nothing but spaces."
            return None

        def __new__(cls, val: str):
            self = super().__new__(cls, val.lower())
            self.validate_text(val)
            return self

        def validate_text(self, text: str) -> bool:
            if (msg := self.get_error_msg(text)) is not None:
                raise ValueError(msg)
            return True

        def to_words(self) -> list[Interpreter.Word]:
            return [Interpreter.Word(s) for s in self.split()]

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
            none: Final[Pattern] = re.compile("^n$|^no$|^none$")
            all: Final[Pattern] = re.compile("^a$|^all$")
            help: Final[Pattern] = re.compile("^h$|^help$")

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
            """get dominant names in Phrase class. Note that dominant names are not defined explicitly in their property, but implicitly by is_dominant_function."""
            return [name for name in cls.Name if cls.is_dominant(name)]

    def __init__(self, range_size: int = 10) -> None:
        self._validate_range(range_max=range_size)
        self.__range: set[int] = set(range(0, range_size))
        self.__input: set[int] = set()
        self.__default_words: set[str] = {" ", "\\-"}.union([str(r) for r in range(0, min(10, range_size + 1))])
        self.__valid_words: list[str] = sorted(self._list_valid_characters())

    def _validate_range(self, range_max: int) -> bool:
        if range_max <= 0 or not isinstance(range_max, int):
            raise ValueError(f"range max must be a positive integer. ={range_max}.")
        return True

    @property
    def input(self) -> set[int]:
        """get current input as a set."""
        return self.__input

    @property
    def range(self) -> set[int]:
        return self.__range

    @property
    def valid_words(self) -> list[str]:
        return self.__valid_words

    @property
    def default_words(self) -> set[str]:
        return self.__default_words

    def clear(self) -> None:
        """Initialize self.__input while self.range remains kept."""
        self.__input.clear()

    def get_input(self) -> list[int]:
        """get the translated input. The output list is sorted and admits no duplicated elements."""
        return sorted(self.input)

    def _is_in_range(self, x: int | set[int]) -> bool:
        """test if the input integer or set of integers is in valid range."""
        return x in self.range if isinstance(x, int) else x.issubset(self.range)

    # def _get_matches(self, pat: Pattern, word: Word) -> list[Match]:
    #     """get the list of re.Match objects that correspond to input pattern and word."""
    #     return list(re.finditer(pat, word))

    def _test_match(self, pat: Pattern, text: Word | Sentence) -> bool:
        """test if the input pair of pattern and word hits something nonempty."""
        return (
            re.search(pat, text) is not None
            if isinstance(text, self.Word)
            else any(re.search(pat, word) is not None for word in text.to_words())
        )

    def _test_match_by(self, pats: list[Pattern], word: Word, eval: Callable[[Iterable], bool] = any) -> bool:
        """An extension of _test_match() to accept many patterns. returns the result processed by the eval function."""
        return eval(self._test_match(pat, word) for pat in pats)

    def _interpret_digit_pattern(self, word: Word, wrt: set[int] = set()) -> set[int]:
        """add digit specified by word to wrt, assuming word corresponds to a digit pattern."""
        return wrt.union(self._get_matched_integers(self.Digit(), word))

    def _interpret_minus_pattern(self, word: Word, wrt: set[int] = set()) -> set[int]:
        """minus digit specified by word to wrt, assuming word corresponds to a minus digit pattern."""
        return wrt.difference(self._get_matched_integers(self.Minus(), word))

    def _interpret_range_pattern(self, word: Word, wrt: set[int] = set()) -> set[int]:
        """add digits to specified by word to wrt, assuming word corresponds to a range pattern."""
        x, y = self._get_matched_integers(self.Range(), word)
        return wrt | set(range(min(x, y), max(x, y) + 1))

    def _get_matched_integers(
        self, match_cls: Interpreter.Digit | Interpreter.Minus | Interpreter.Range, word: Word
    ) -> list[int]:
        """get list of integers when the pair of pattern (of match_cls) and word hits something meaningful."""
        return (
            [int(match.group(call)) for call in match_cls.calls]
            if (match := re.search(match_cls.pat, word)) is not None
            else []
        )

    def _get_matched_phrase(self, word: Word) -> Phrase.Name:
        """get the first hit phrase in word. Error if it hits no phrases."""
        for name in self.Phrase.Name:
            if self._test_match(self.Phrase.get_pattern(name), word):
                return name
        raise Exception(f"{word} does not match any of {self.Phrase.__name__}.")

    def _interpret_phrase(self, word: Word) -> set[int]:
        """get set of integers meant by phrase in word. an error wil be raised if word is not a phrase."""
        match self._get_matched_phrase(word):  # raise error if it is not a phrase
            case self.Phrase.Name.ALL:
                return self.range
            case self.Phrase.Name.NONE:
                return set()
        raise Exception(f"{word} is not a phrase.")

    def _exist_dominant_phrase(self, sentence: Sentence) -> bool:
        """test if word has a dominant phrase."""
        return any(
            itertools.chain.from_iterable(
                [self._test_match(self.Phrase.get_pattern(d_name), word) for d_name in self.Phrase.get_dominant_names()]
                for word in sentence.to_words()
            )
        )

    def _find_most_dominant_phrase(self, sentence: Sentence) -> Phrase.Name:
        """get the most dominant phrase in sentence."""
        d_phrases = [
            name
            for name in self.Phrase.get_dominant_names()
            if self._test_match(self.Phrase.get_pattern(name), sentence)
        ]
        if len(d_phrases) == 0:
            raise ValueError(f"No dominant phrase are found in {sentence}")
        return d_phrases[0]

    def _list_valid_characters(self) -> set[str]:
        """get the possible characters for input. It is defined as the set {numerical characters in range} | {space and -} | {characters in phrase}."""
        # default set consists of numerical characters and space and -.
        # it is at self.__default_words
        # characters in phrase
        pat: Pattern = re.compile("[a-z]")
        src: str = self.Phrase.Pat.all.pattern + self.Phrase.Pat.none.pattern + self.Phrase.Pat.help.pattern
        return set([m.group(0) for m in re.finditer(pat, src)]).union(self.default_words)

    def test_valid_characters(self, sentence: Sentence) -> bool:
        """test if input sentence is free of invalid characters"""
        pat: Pattern = re.compile(f"[^{''.join(self.valid_words)}]")
        return re.search(pat, sentence) is None

    def _get_maximum_valid_length(self, scale: int = 5) -> int:
        return max(self.range) * scale

    def test_valid_length(self, sentence: Sentence) -> bool:
        """test if input sentence is of reasonable length."""
        return len(sentence) <= self._get_maximum_valid_length()

    def get_invalid_words(self, sentence: Sentence) -> list[Word]:
        pats: list[Pattern] = [self.Phrase.get_pattern(name) for name in self.Phrase.Name] + [
            self.Digit.pat,
            self.Minus.pat,
            self.Range.pat,
        ]
        return [word for word in sentence.to_words() if not self._test_match_by(pats, word)]

    def _interpret(self, sentence: Sentence, wrt: set[int] = set()) -> set[int]:
        """get set of integers meant by sentence, assuming there is no dominant phrases that supersede integer interpretation."""
        for word in sentence.to_words():
            # if it is a phrase
            if self._test_match_by([self.Phrase.Pat.all, self.Phrase.Pat.none], word):
                wrt = self._interpret_phrase(word)
            # digit
            elif self._test_match(self.Digit.pat, word):
                wrt = self._interpret_digit_pattern(word, wrt)
            # minus
            elif self._test_match(self.Minus.pat, word):
                wrt = self._interpret_minus_pattern(word, wrt)
            # range
            elif self._test_match(self.Range.pat, word):
                wrt = self._interpret_range_pattern(word, wrt)
            else:
                raise ValueError(f"{word} in {sentence} can't be interpreted.")
        return wrt

    def interpret(self, sentence: Sentence) -> set[int] | Phrase.Name:
        # check exist dominant phrase
        if self._exist_dominant_phrase(sentence):
            phrase: Interpreter.Phrase.Name = self._find_most_dominant_phrase(sentence)
            if phrase == Interpreter.Phrase.Name.HELP:
                return phrase
            else:
                raise ValueError(f"Unknown dominant phrase {phrase}.")
        # now we assume that input means some digits
        return self._interpret(sentence=sentence)
