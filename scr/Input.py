import click
from rich import print


class Input_lines:
    def __init__(self) -> None:
        self.input: list[int] = []

    def get_input(self) -> list[int]:
        return self.input

    def __validate_input(self, x: list[int], range: list[int]) -> bool:
        for v in x:
            if abs(v) not in range:
                raise ValueError(f"{v} is too big. maximum value for this line is {range}")
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
