import abc
from typing import Optional

from rich import print

from Mediator import Candidate, Mediator, Option
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

    def _show_candidates(self, line: Paged_Text_Line, candidates: list[Candidate]) -> None:
        """print correction candidates (for a given row with dust)."""
        display: str = "\n".join([f"{c.idx} | {c.text}" for c in candidates])
        print(f"\n{line.text}\n\n{display}\n")

    def _find_candidate(self, idx: int, candidates: list[Candidate]) -> Candidate:
        """find a condidate with asked idx."""
        for c in candidates:
            if c.idx == idx:
                return c
        raise ValueError(f"there is no candidates with idx={idx} in {candidates}")

    def choose_from_integers(self) -> Paged_Text_Lines:
        """from diplayed candidates, interactively choose one, and return updated lines."""
        new_lines: list[Paged_Text_Line] = []
        delete_idx: list[int] = []
        if len(self.lines) > 0:
            self.mediator.explain()
        rows: list[Paged_Text_Line] = self.find_rows()
        print(f"{len(rows)} cases found.")
        for i, line in enumerate(rows):
            candidates: list[Candidate] = self._get_candidates(line)
            self._show_candidates(line, candidates)
            msg: Optional[str] = None if i == 0 else f"({(i+1)}/{len(rows)})"
            user_input, flag = self.mediator.get_user_input(
                msg=msg, default_value=Option.Pass.value, domain=range(len(candidates))
            )
            choice = self.mediator.interpret(user_input=user_input, flag=flag)
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
