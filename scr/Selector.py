from rich import print

from Extractor import Extractor, Text_Lines
from Inputter import Inputter


class Line_Selector:
    def __init__(self, lines: Text_Lines = Text_Lines(), max_line: int = 10) -> None:
        self.max_line: int = max_line
        self.lines: Text_Lines = lines
        # self.inp: Input_lines = Input_lines()
        self.inp: Inputter = Inputter(max_line)

    def read_Text_Lines(self, text: Text_Lines) -> None:
        self.lines = text

    def select_lines_to_delete(self) -> Text_Lines:
        L: int = len(self.lines)
        delete_idx: list[int] = []
        adds: int = 0
        print(f"{L} cases found.")
        total: int = L // self.max_line + 1
        for set in range(0, total):
            start: int = set * self.max_line
            end: int = min((set + 1) * self.max_line, L)
            if start >= end:
                break
            # show header one time
            with_header: bool = set == 0
            self.lines.print(start, end, with_header=with_header, with_page_idx=False)
            # ask user to enter line indexes to delete
            self.inp.prompt(msg=f"({set+1}/{total}): Enter N to delete (n/-n/m-n/a[ll]/n[one])")
            # pool deleting idx
            eff_choice: list[int] = sorted(self.inp.input.intersection(range(0, min(self.max_line, L - adds))))
            selected_idx: list[int] = [self.lines.get_row_idx(i + adds) for i in eff_choice]
            print(f"range={self.inp.range}")
            print(f"select [magenta]{eff_choice}[/]")
            print(f"delete {selected_idx}")
            delete_idx.extend(selected_idx)
            adds += self.max_line
        return self.lines.select(rows=delete_idx)


def delete_digit_only_pages(text: list[str]) -> Text_Lines:
    extractor = Extractor(text)
    lines_digits: Text_Lines = extractor.get_digit_only_lines()
    lines_to_delete: Text_Lines = Line_Selector(lines_digits, max_line=10).select_lines_to_delete()
    return Text_Lines(text) - lines_to_delete


# testing
def test(text: list[str]) -> Text_Lines:
    e = Extractor(text)
    lines_cand: Text_Lines = e.get_digit_only_lines() + e.get_unexpected_front_matter_pages()
    ls = Line_Selector(lines_cand, max_line=10)
    lines_to_delete: Text_Lines = ls.select_lines_to_delete()
    return Text_Lines(text) - lines_to_delete


def main():
    with open("./scr/MCSM_clean.txt") as f:
        text = f.read()
        res: Text_Lines = test(text.splitlines())
        print("cleaned lines")
        res.print()
        with open("./scr/MCSM_clean_last.txt", mode="w") as tf:
            tf.write(res.to_text())


if __name__ == "__main__":
    main()
