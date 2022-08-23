from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, IntEnum, auto
from re import Pattern
from typing import Callable, Optional

import click
from rich import print
from typing_extensions import Self

from Text_Line import Paged_Text_Line
from Text_Lines import Paged_Text_Lines, Texts_Printer


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

    def interpret(self, user_input: int | str, flag: Mediator.Integer_Flag) -> Choice:
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
        msg: str = "enter action. default =",
        allow_suggest: bool = True,
        default_value: int | str = Option.Pass.value,
        show_msg: bool = True,
    ) -> tuple[int | str, Mediator.Integer_Flag]:
        """ask user to enter some input that represents her choice."""
        msg = msg if show_msg else ""
        while True:
            ret: tuple[int | str | None, Mediator.Integer_Flag] = click.prompt(
                text=msg, type=str | int, value_proc=self._convert_input, default=default_value
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
    def __init__(self, lines_ref: Paged_Text_Lines, default_value: str = Option.Pass.value) -> None:
        self._lines_ref: Paged_Text_Lines = lines_ref
        self.default_value: str = default_value

    def suggest(self, line: Paged_Text_Line) -> str:
        """suggest default page-number for the given line"""
        arounds: Paged_Text_Lines = self._lines_ref.get_rows_around(line=line, radius=1)
        if len(arounds) == 0:
            return self.default_value

        # set default value
        default_value: str = self.default_value
        for around in reversed(arounds):
            # prioritize the successor row here just for my preference
            if around.page_number is not None:
                default_value = str(around.page_number)
                break
        return default_value

    def get_processed_suggestion(
        self,
        line: Paged_Text_Line,
        processor: Callable[[str, Paged_Text_Line], str],
        condition: Callable[[str, Paged_Text_Line], bool],
    ) -> str:
        suggested: str = self.suggest(line)
        return processor(suggested, line) if condition(suggested, line) else suggested


class Fill:
    def __init__(
        self,
        lines_blank_page_number: Paged_Text_Lines,
        lines_ref: Paged_Text_Lines,
    ) -> None:
        self._lines: Paged_Text_Lines = lines_blank_page_number
        self._lines_ref: Paged_Text_Lines = lines_ref
        self.mediator: Mediator = Mediator(public_options=["p", "r"], private_options=["f"])
        self.suggest: Suggester = Suggester(lines_ref=lines_ref, default_value=Option.Pass.value)
        self.printer = Texts_Printer()

    def get_filled_lines(self) -> Paged_Text_Lines:
        """interactively ask user to fill numbers in rows of missing page number. return the filled lines object."""
        new_lines: list[Paged_Text_Line] = []
        delete_idx: list[int] = []
        if len(self._lines) > 0:
            self.mediator.explain()
        for i, line in enumerate(self._lines):
            self.printer.print_around(self._lines_ref, row=line.idx, N_around=1)
            user_input, flag = self.mediator.get_user_input(show_msg=(i == 0), default_value=self.suggest.suggest(line))
            choice = self.mediator.interpret(user_input=user_input, flag=flag)
            # if suggest is chosen, ask user to re-input
            # if choice.option == Option.Suggest:
            #     choice = self.suggest.suggest(line)
            match choice.option:
                case Option.Pass:
                    continue
                case Option.Fill:
                    line.page_number = choice.number
                    new_lines.append(line)
                case Option.Remove:
                    delete_idx.append(line.idx)
                case _:
                    raise Exception(f"unknown choice type {choice.option}.")
        return self._lines_ref.exclude(delete_idx).overwrite(new_lines)


class Correct:
    def __init__(
        self,
        lines_strange_page_number: Paged_Text_Lines,
        lines_ref: Paged_Text_Lines,
        ignore: list[int] = [],
        append_key: list[str] = ["chapter", "part", "section"],
    ) -> None:
        self._lines: Paged_Text_Lines = lines_strange_page_number
        self._lines_ref: Paged_Text_Lines = lines_ref
        self._ignore: list[int] = ignore
        self.mediator: Mediator = Mediator(public_options=["p", "r"], private_options=["f", "a"])
        self.suggest: Suggester = Suggester(lines_ref=lines_ref)
        self.printer = Texts_Printer()
        self.pat_append: Pattern = re.compile("|".join([f"({key})" for key in append_key]))

    def _test_to_append(self, suggested: str, line: Paged_Text_Line) -> bool:
        return re.search("^\\d+$", suggested) is not None and re.search(self.pat_append, line.text.lower()) is not None

    def get_suggestion(self, line: Paged_Text_Line) -> str:
        return self.suggest.get_processed_suggestion(
            line, processor=lambda s, _: "+" + s, condition=self._test_to_append
        )

    def get_corrected_lines(self) -> Paged_Text_Lines:
        """interactively ask user to fill numbers in rows of missing page number. return the filled lines object."""
        new_lines: list[Paged_Text_Line] = []
        delete_idx: list[int] = []
        if len(self._lines) > 0:
            self.mediator.explain()
        for i, line in enumerate(self._lines):
            self.printer.print_around(self._lines_ref, row=line.idx, N_around=1)
            user_input, flag = self.mediator.get_user_input(show_msg=(i == 0), default_value=self.get_suggestion(line))
            choice = self.mediator.interpret(user_input=user_input, flag=flag)
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
                    raise Exception(f"unknown choice type {choice.option}.")
        return self._lines_ref.exclude(delete_idx).overwrite(new_lines)
