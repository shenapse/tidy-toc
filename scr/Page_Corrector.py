from __future__ import annotations

import re
from re import Pattern
from typing import Callable

from Mediator import Mediator, Option
from Text_Line import Paged_Text_Line
from Text_Lines import Paged_Text_Lines, Texts_Printer


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
        self.mediator: Mediator = Mediator(
            public_options=[Option.Pass.value, Option.Remove.value], private_options=[Option.Digit.value]
        )
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
                case Option.Digit:
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
        self.mediator: Mediator = Mediator(
            public_options=[Option.Pass.value, Option.Remove.value],
            private_options=[Option.Digit.value, Option.Append.value],
        )
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
                case Option.Digit:
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
