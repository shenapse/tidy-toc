from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, IntEnum, auto
from re import Pattern
from typing import Optional

import click
from rich import print
from typing_extensions import Self

from Text_Line import Paged_Text_Line
from Text_Lines import Paged_Text_Lines


class Option(Enum):
    Pass = "p"
    Fill = "f"
    Append = "a"
    Suggest = "s"
    Remove = "r"


@dataclass
class Choice:
    option: Option
    number: int


class Page_Interpreter:
    _highlight: str = "magenta"
    _pat_digit: Pattern = re.compile("^[+-]?\\d+$")
    _pat_plus: Pattern = re.compile("^[+]\\d+$")

    class Integer_Flag(IntEnum):
        """record if integer is provided with '+' sign."""

        Plus = auto()
        Normal = auto()

        @classmethod
        def get_flag(cls, x: str) -> Self:
            return cls.Plus if re.search(Page_Interpreter._pat_plus, x) else cls.Normal

    def __init__(self, private_options: list[str] = ["a", "f"], max_page: int = 10000) -> None:
        self._public_options: list[str] = [opt.value for opt in Option if opt.value not in private_options]
        self._private_options: list[str] = [opt.value for opt in Option if opt.value in private_options]
        self._max_page: int = max_page

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

    def _generate_color_block(self) -> tuple[str, str]:
        return f"[{self._highlight}]", "[/]"

    def get_public_options(self) -> list[Option]:
        return [opt for opt in Option if opt.value in self._public_options]

    def get_private_options(self) -> list[Option]:
        return [opt for opt in Option if opt.value in self._private_options]

    def explain(self) -> None:
        begin, end = self._generate_color_block()
        explain_options: str = ", ".join([f"{opt.value}: {begin}{opt.name}{end}" for opt in self.get_public_options()])
        explain_integer: str = f"enter {begin}Integer{end}"
        msg: str = ", ".join([explain_integer, explain_options])
        print(msg)

    def interpret(self, user_input: int | str, flag: Page_Interpreter.Integer_Flag) -> Choice:
        """convert user-input integer via click into choice object."""
        if isinstance(user_input, int):
            # fill user input. flag tells us which option should be used.
            option: Option = Option.Append if flag == Page_Interpreter.Integer_Flag.Plus else Option.Fill
            return Choice(option=option, number=user_input)
        # other options are simply converted back to option objects
        # their number property are not interesting
        for option in self.get_public_options():
            if user_input == option.value:
                return Choice(option=option, number=0)
        raise ValueError(f"Unknown option. {user_input}")

    def get_user_input(
        self, allow_suggest: bool = True, default_value: int | str = Option.Pass.value
    ) -> tuple[int | str, Page_Interpreter.Integer_Flag]:
        """ask user to enter some input that represents her choice."""
        while True:
            ret: tuple[int | str | None, Page_Interpreter.Integer_Flag] = click.prompt(
                text="enter action. default =", type=str | int, value_proc=self._convert_input, default=default_value
            )
            inp, flag = ret
            if inp is None:
                continue
            if isinstance(inp, int) and not self._test_range(value=inp):
                print(f"input integer x must be {-self._max_page}<=x<={self._max_page}.")
                continue
            elif not allow_suggest and inp == Option.Suggest.value:
                print("no more suggestion.")
                continue
            return inp, flag


class Suggester:
    def __init__(
        self, inter: Page_Interpreter, lines_blank_page_number: Paged_Text_Lines, lines_ref: Paged_Text_Lines
    ) -> None:
        self._inter: Page_Interpreter = inter
        self._lines: Paged_Text_Lines = lines_blank_page_number
        self._lines_ref: Paged_Text_Lines = lines_ref

    def _get_neighoring_lines(self, line: Paged_Text_Line) -> list[Paged_Text_Line]:
        """get neighboring two rows relative to input line object in original lines object.
        this method is intended to be called triggered by choice == suggest"""
        idx: int = self._lines_ref.search(line.idx)
        if idx == -1:
            raise Exception(f"{line} is not found in {self._lines_ref}.")
        return [self._lines_ref[i] for i in [idx - 1, idx + 1] if 0 <= i < self._lines_ref.len()]

    def suggest(self, line: Paged_Text_Line) -> Choice:
        """search neighboring rows of input line and show them to user, and then ask input again.
        this method is called triggered by choice==suggest, and can't be called successively.
        """
        neibs: list[Paged_Text_Line] = self._get_neighoring_lines(line)
        if len(neibs) == 0:
            print(f"no rows are found near {line}")
            user_input, flag = self._inter.get_user_input(allow_suggest=False)
            return self._inter.interpret(user_input=user_input, flag=flag)
        # show these surrounding lines
        print("it's between")
        for neib in neibs:
            neib.print()
        # set default value
        default_value: int = 0
        for neib in reversed(neibs):
            # prioritize the successor row here just for my preference
            if neib.page_number is not None:
                default_value = neib.page_number
                break
        # further suggestion is not allowed
        user_input, flag = self._inter.get_user_input(allow_suggest=False, default_value=str(default_value))
        return self._inter.interpret(user_input=user_input, flag=flag)


class Fill:
    def __init__(
        self,
        lines_blank_page_number: Paged_Text_Lines,
        lines_ref: Paged_Text_Lines,
    ) -> None:
        self._lines: Paged_Text_Lines = lines_blank_page_number
        self._lines_ref: Paged_Text_Lines = lines_ref
        self.inter: Page_Interpreter = Page_Interpreter(private_options=["f", "a"])
        self.suggest: Suggester = Suggester(
            inter=self.inter, lines_blank_page_number=lines_blank_page_number, lines_ref=lines_ref
        )

    def get_filled_lines(self) -> Paged_Text_Lines:
        """interactively ask user to fill numbers in rows of missing page number. return the filled lines object."""
        new_lines: list[Paged_Text_Line] = []
        delete_idx: list[int] = []
        if self._lines.len() > 0:
            self.inter.explain()
        for line in self._lines:
            line.print()
            user_input, flag = self.inter.get_user_input()
            choice = self.inter.interpret(user_input=user_input, flag=flag)
            # if suggest is chosen, ask user to re-input
            if choice.option == Option.Suggest:
                choice = self.suggest.suggest(line)
            match choice.option:
                case Option.Pass:
                    continue
                case Option.Fill:
                    line.page_number = choice.number
                    new_lines.append(line)
                case Option.Remove:
                    delete_idx.append(line.idx)
                case _:
                    raise Exception(f"unknow choice type {choice.option}.")
        return self._lines.exclude(delete_idx).overwrite(new_lines)


class Correct:
    def __init__(
        self, lines_strange_page_number: Paged_Text_Lines, lines_ref: Paged_Text_Lines, ignore: list[int] = []
    ) -> None:
        self._lines: Paged_Text_Lines = lines_strange_page_number
        self._lines_ref: Paged_Text_Lines = lines_ref
        self._ignore: list[int] = ignore
        self.inter: Page_Interpreter = Page_Interpreter(private_options=["f", "a"])
        self.suggest: Suggester = Suggester(
            inter=self.inter, lines_blank_page_number=lines_strange_page_number, lines_ref=lines_ref
        )

    def get_corrected_lines(self) -> Paged_Text_Lines:
        """interactively ask user to fill numbers in rows of missing page number. return the filled lines object."""
        new_lines: list[Paged_Text_Line] = []
        delete_idx: list[int] = []
        if self._lines.len() > 0:
            self.inter.explain()
        for line in self._lines:
            line.print()
            user_input, flag = self.inter.get_user_input()
            choice = self.inter.interpret(user_input=user_input, flag=flag)
            # if suggest is chosen, ask user to re-input
            if choice.option == Option.Suggest:
                choice = self.suggest.suggest(line)
            match choice.option:
                case Option.Pass:
                    continue
                case Option.Fill:
                    line.page_number = choice.number
                    new_lines.append(line)
                case Option.Append:
                    text: str = line.to_text()
                    line.page_number = choice.number
                    line.text = text
                    new_lines.append(line)
                case Option.Remove:
                    delete_idx.append(line.idx)
                case _:
                    raise Exception(f"unknow choice type {choice.option}.")
        return self._lines.exclude(delete_idx).overwrite(new_lines)
