from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, IntEnum, auto
from re import Pattern
from typing import Iterable, Optional

import click
from rich import print
from typing_extensions import Self

from Text_Lines import Texts_Printer


@dataclass
class Candidate:
    text: str
    idx: int

    @classmethod
    def to_candidate(cls, candidates: list[str]) -> list[Self]:
        return [Candidate(text=c, idx=i) for i, c in enumerate(candidates)]


class Option(Enum):
    Pass = "p"
    Fill = "f"
    Append = "a"
    Remove = "r"


@dataclass
class Choice:
    option: Option
    number: int


class Mediator:
    _pat_digit: Pattern = re.compile("^[+-]?\\d+$")
    _pat_plus: Pattern = re.compile("^[+]\\d+$")

    class Integer_Flag(IntEnum):
        """record if integer is provided with '+' sign."""

        Plus = auto()
        Normal = auto()

        @classmethod
        def get_flag(cls, x: str) -> Self:
            return cls.Plus if re.search(Mediator._pat_plus, x) else cls.Normal

    def __init__(
        self, public_options: list[str] = ["p", "r"], private_options: list[str] = ["f"], max_page: int = 10000
    ) -> None:
        self._public_options: list[str] = [opt.value for opt in Option if opt.value in public_options]
        self._private_options: list[str] = [opt.value for opt in Option if opt.value in private_options]
        self._max_page: int = max_page
        self._printer = Texts_Printer()

    def _test_digit(self, text: str) -> bool:
        return re.search(self._pat_digit, text) is not None

    def _test_range(self, value: int, int_min: Optional[int] = None, int_max: Optional[int] = None) -> bool:
        int_min = -self._max_page if int_min is None else int_min
        int_max = self._max_page if int_max is None else int_max
        return int_min <= value <= int_max

    def _convert_input(self, inp: str) -> tuple[Optional[int | str], Integer_Flag]:
        """try to convert input into some assumed type.
        None is the signature of failure, in which case input should be asked for user again.
        """
        # inp = inp.lower() if isinstance(inp, str) else inp
        flag_default = self.Integer_Flag.Normal
        if self._test_digit(inp):
            return int(inp), self.Integer_Flag.get_flag(inp)
        elif inp in self._public_options:
            return inp, flag_default
        else:
            print(f"invalid string. use {self._public_options}.")
        # otherwise
        return None, flag_default

    def get_public_options(self) -> list[Option]:
        return [opt for opt in Option if opt.value in self._public_options]

    def get_private_options(self) -> list[Option]:
        return [opt for opt in Option if opt.value in self._private_options]

    def explain(self) -> None:
        begin, end = self._printer.generate_color_block()
        explain_options: str = ", ".join([f"{opt.value}: {begin}{opt.name}{end}" for opt in self.get_public_options()])
        explain_integer: str = f"enter {begin}Integer{end}"
        msg: str = ", ".join([explain_integer, explain_options])
        print(msg)

    def interpret(self, user_input: int | str, flag: Mediator.Integer_Flag = Integer_Flag.Normal) -> Choice:
        """convert user-input integer via click into choice object."""
        if isinstance(user_input, int):
            # fill user input. flag tells us which option should be used.
            option: Option = Option.Append if flag == Mediator.Integer_Flag.Plus else Option.Fill
            return Choice(option=option, number=user_input)
        # other options are simply converted back to option objects
        # their number property are not interesting
        for option in self.get_public_options():
            if user_input == option.value:
                return Choice(option=option, number=0)
        raise ValueError(f"Unknown option. {user_input}")

    def get_user_input(
        self,
        msg: Optional[str] = None,
        default_value: int | str = Option.Pass.value,
        domain: Optional[Iterable[int]] = None,
        show_msg: bool = True,
    ) -> tuple[int | str, Mediator.Integer_Flag]:
        """ask user to enter some input that represents her choice."""
        msg = "enter action. default =" if msg is None else msg
        msg = msg if show_msg else ""
        while True:
            ret: tuple[int | str | None, Mediator.Integer_Flag] = click.prompt(
                text=msg, type=str | int, value_proc=self._convert_input, default=default_value
            )
            inp, flag = ret
            if inp is None:
                continue
            if isinstance(inp, int):
                if domain is not None and inp not in (d := list(domain)):
                    print(f"input integer x must be in {d}.")
                    continue
                if not self._test_range(value=inp):
                    print(f"input integer x must be {-self._max_page}<=x<={self._max_page}.")
                    continue
            return inp, flag
