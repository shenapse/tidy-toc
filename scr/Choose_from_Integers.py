import abc
from typing import Optional

from rich import print

from Mediator import Candidate, Choice, Mediator, Option
from Text_Line import Paged_Text_Line
from Text_Lines import Paged_Text_Lines


class Choose_from_Integers(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self, lines: Paged_Text_Lines) -> None:
        self.lines: Paged_Text_Lines = lines
        self.mediator = Mediator(public_options=["p", "r"], private_options=["f"])
        raise NotImplementedError

    @abc.abstractmethod
    def find_rows(self) -> list[Paged_Text_Line]:
        raise NotImplementedError

    @abc.abstractmethod
    def _get_candidates(self, line: Paged_Text_Line) -> list[Candidate]:
        raise NotImplementedError

    def _test_trivial_candidate(self, line: Paged_Text_Line, candidates: list[Candidate]) -> bool:
        return False

    def _get_forced_choice(self, line: Paged_Text_Line, candidates: list[Candidate]) -> Choice:
        raise NotImplementedError

    def _show_candidates(self, line: Paged_Text_Line, candidates: list[Candidate]) -> None:
        """print correction candidates (for a given row with dust)."""
        display: str = "\n".join([f"{c.idx} | {c.text}" for c in candidates])
        print(f"\n{line.text}\n\n{display}\n")

    def _find_candidate(self, idx: int, candidates: list[Candidate]) -> Candidate:
        """find a candidate with asked idx."""
        for c in candidates:
            if c.idx == idx:
                return c
        raise ValueError(f"there is no candidates with idx={idx} in {candidates}")

    def _get_what_chosen(self, choice: Choice) -> str:
        """generate string that describes the choice for printing it."""
        if choice.option == Option.Fill:
            return "this"
        if choice.option in [Option.Pass, Option.Remove]:
            return choice.option.value
        raise ValueError(f"unknown type of choice {choice}")

    def _get_choice(self, line: Paged_Text_Line, candidates: list[Candidate], msg: Optional[str] = None) -> Choice:
        if self._test_trivial_candidate(line, candidates):
            choice = self._get_forced_choice(line, candidates)
            print(f"trivial candidate. auto-choose {self._get_what_chosen(choice=choice)}.")
            return choice
        user_input, _ = self.mediator.get_user_input(
            msg=msg, default_value=Option.Pass.value, domain=range(len(candidates))
        )
        return self.mediator.interpret(user_input=user_input)

    def choose_from_integers(self) -> Paged_Text_Lines:
        """from displayed candidates, interactively choose one, and return updated lines."""
        new_lines: list[Paged_Text_Line] = []
        delete_idx: list[int] = []
        if len(self.lines) > 0:
            self.mediator.explain()
        rows: list[Paged_Text_Line] = self.find_rows()
        print(f"{len(rows)} cases found.")
        for i, line in enumerate(rows):
            candidates: list[Candidate] = self._get_candidates(line)
            if len(candidates) > 0:
                self._show_candidates(line, candidates)
            msg: Optional[str] = None if i == 0 else f"({(i+1)}/{len(rows)})"
            choice = self._get_choice(line, candidates, msg)
            match choice.option:
                case Option.Pass:
                    continue
                case Option.Fill:
                    line.text = self._find_candidate(idx=choice.number, candidates=candidates).text
                    new_lines.append(line)
                case Option.Remove:
                    delete_idx.append(line.idx)
                case _:
                    raise Exception(f"unknown choice type {choice.option}.")
        return self.lines.exclude(delete_idx).overwrite(new_lines)
