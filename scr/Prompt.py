import abc

import click
from rich import print

from Interpreter import Interpreter


class _Input(metaclass=abc.ABCMeta):
    @abc.abstractclassmethod
    def prompt(self, msg: str = "") -> None:
        raise NotImplementedError

    @abc.abstractclassmethod
    def get_input(self) -> list[int]:
        raise NotImplementedError


class Prompt(_Input):
    def __init__(self) -> None:
        self._input: set[int] = set()

    @property
    def input(self) -> set[int]:
        return self._input

    def get_input(self) -> list[int]:
        return sorted(self.input)

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
            res_interpreted: set[int] | inter.Phrase.Name = inter.interpret(sentence)
            # check if input contains a dominant phrase
            if isinstance(res_interpreted, set):
                self._input = res_interpreted
                break
