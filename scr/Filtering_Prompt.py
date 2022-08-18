import click
from rich import print

from Input import _Input
from Interpreter import Interpreter


class Prompt(_Input):
    def __init__(self) -> None:
        self._input: set[int] = set()

    @property
    def input(self) -> set[int]:
        return self._input

    def get_input(self) -> list[int]:
        return sorted(self.input)

    def _get_highlighted(self, text: str, color: str = "magenda") -> str:
        return f"[{color}]{text}[/]"

    def print_help(self, highlight: str = "magenda") -> None:
        print("Inputs are interpreted sequentially from left to right.")
        print(f"1 6 4   ->   {self._get_highlighted('[1, 4, 6]', color=highlight)}")
        print(f"3-6     ->   {self._get_highlighted('[3, 4, 5, 6]', color=highlight)}")
        print(f"2-5 -4  ->   {self._get_highlighted('[2, 3, 5]', color=highlight)}")
        print(f"n       ->   {self._get_highlighted('[]', color=highlight)}")
        print(f"all     ->   {self._get_highlighted('all listed numbers', color=highlight)}")

    def prompt(self, inter: Interpreter, msg: str = "") -> None:
        """ask user to type input in CLI repeatedly until it gets a valid one."""
        while True:
            raw_input: str = click.prompt(msg, type=str)
            # if raw input can be turned into sentence
            if not Interpreter.Sentence.is_sentenceable(raw_input):
                print(Interpreter.Sentence.get_error_msg(raw_input))
                continue
            sentence = inter.Sentence(raw_input)
            # length and character check
            if not inter.test_valid_length(sentence):
                print(f"Invalid length. length must be <= {inter._get_maximum_valid_length()}.")
                continue
            elif not inter.test_valid_characters(sentence):
                print(f"Invalid characters. Use from {inter.valid_words}.")
                continue
            # check sentence consists only of valid words
            ng_words: list[inter.Word] = inter.get_invalid_words(sentence)
            if ng_words != []:
                print(f"invalid input found.{','.join(ng_words)}")
                continue
            interpreted: set[int] | inter.Phrase.Name = inter.interpret(sentence)
            # check if input contains a dominant phrase
            if isinstance(interpreted, inter.Phrase.Name):
                # get a dominant phrase HELP
                self.print_help()
            elif isinstance(interpreted, set):
                if not inter._is_in_range(interpreted):
                    print(f"input must be included in range={inter.range}")
                    continue
                self._input = interpreted
                break
