from rich import print

from Extractor import Extractor, Text_Lines
from Interpreter import Interpreter, Prompt


class Line_Selector:
    def __init__(self, lines: Text_Lines = Text_Lines(), max_line: int = 10) -> None:
        self._validate_max_line(max_line=max_line)
        self.max_line: int = max_line
        self.lines: Text_Lines = lines

    def _validate_max_line(self, max_line: int) -> bool:
        if max_line <= 0 or not isinstance(max_line, int):
            raise ValueError(f"max line must be a positive integer. max_line={max_line}.")
        return True

    def read_Text_Lines(self, text: Text_Lines) -> None:
        self.lines = text

    def _get_starting_idx(self, n_th_zero_start: int) -> int:
        """get the starting position of idx of self.lines for n-th loop."""
        return n_th_zero_start * self.max_line

    def _get_corresponding_row_idx_in_lines(self, n_th_zero_start: int, idx: list[int]) -> list[int]:
        idx_start: int = self._get_starting_idx(n_th_zero_start)
        return [self.lines.get_row_idx(i + idx_start) for i in idx]

    def _get_effective_range(self, n_th_zero_start: int) -> set[int]:
        """get the"""
        length: int = len(self.lines)
        number_of_remaining_rows: int = length - self._get_starting_idx(n_th_zero_start)
        return set(range(0, min(self.max_line, number_of_remaining_rows)))

    def _validate_same_range(self, inter: Interpreter) -> bool:
        if self.max_line != len(inter.range):
            raise ValueError(f"self.max_line={self.max_line} while inter.range = {inter.range}")
        return True

    def select_lines_to_delete(self, inter: Interpreter, prompt: Prompt) -> Text_Lines:
        self._validate_same_range(inter=inter)
        L: int = len(self.lines)
        print(f"{L} cases found.")
        delete_idx: list[int] = []
        total: int = L // self.max_line + 1
        for i in range(0, total):
            start: int = i * self.max_line
            end: int = min((i + 1) * self.max_line, L)
            if start >= end:
                break
            # show header one time
            with_header: bool = set == 0
            self.lines.print(start, end, with_header=with_header, with_page_idx=False)
            # ask user to enter line indexes to delete
            prompt.prompt(inter=inter, msg=f"({i+1}/{total}): Enter N to delete (n/-n/m-n/a[ll]/n[one])")
            # convert selected list of integer like [0,1,4,6] to corresponding row idx of lines such as [20, 21, 24, 26]
            choice_in_range: list[int] = sorted(prompt.input.intersection(self._get_effective_range(n_th_zero_start=i)))
            selected_row_idx: list[int] = self._get_corresponding_row_idx_in_lines(i, choice_in_range)
            print(f"range={inter.range}")
            print(f"select [magenta]{choice_in_range}[/]")
            # print(f"delete {selected_row_idx}")
            delete_idx.extend(selected_row_idx)
        return self.lines.select(rows=delete_idx)


# testing
def test2(text: list[str]) -> Text_Lines:
    max_line: int = 10
    inter = Interpreter(range_max=max_line)
    prompt = Prompt()
    e = Extractor(text)
    lines_cand: Text_Lines = e.get_digit_only_lines() + e.get_unexpected_front_matter_pages()
    ls = Line_Selector(lines_cand, max_line=10)
    lines_to_delete: Text_Lines = ls.select_lines_to_delete(inter=inter, prompt=prompt)
    return Text_Lines(text) - lines_to_delete


def test(text: list[str]) -> Text_Lines:
    max_line: int = 10
    inter = Interpreter(range_max=max_line)
    prompt = Prompt()
    e = Extractor(text)
    lines_cand: Text_Lines = e.get_digit_only_lines() + e.get_unexpected_front_matter_pages()
    ls = Line_Selector(lines_cand, max_line=10)
    lines_to_delete: Text_Lines = ls.select_lines_to_delete(inter=inter, prompt=prompt)
    return Text_Lines(text) - lines_to_delete


def main():
    with open("./scr/Algebra_clean.txt") as f:
        text = f.read()
        res: Text_Lines = test(text.splitlines())
        res.print()
        # with open("./scr/MCSM_clean.txt", mode="w") as tf:
        #     tf.write(res.to_text())


if __name__ == "__main__":
    main()
