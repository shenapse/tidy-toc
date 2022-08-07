from Extractor import Extractor, Text_Lines
from scr.Inputs import Input_lines


class Line_Selector:
    def __init__(self, lines: Text_Lines = Text_Lines(), max_line: int = 10) -> None:
        self.max_line = max_line
        self.lines: Text_Lines = lines
        self.inp: Input_lines = Input_lines()

    def read_Text_Lines(self, text: Text_Lines) -> None:
        self.lines = text

    def select_lines_to_delete(self) -> Text_Lines:
        L: int = len(self.lines)
        delete_idx: list[int] = []
        adds: int = 0
        for set in range(0, L // self.max_line + 1):
            start: int = set * self.max_line
            end: int = min((set + 1) * self.max_line, L)
            if start >= end:
                break
            # show part of lines for the first set only
            with_header: bool = set == 0
            self.lines.print(start, end, with_header)
            # ask user to enter line indexes to delete
            self.inp.prompt(msg="enter N to delete (N/-N/all/none)", range=list(range(0, min(self.max_line, L - adds))))
            # pool deleting idx
            selected_idx: list[int] = [self.lines.get_row_idx(i + adds) for i in self.inp.get_input()]
            print(f"select {selected_idx}")
            delete_idx.extend(selected_idx)
            adds += self.max_line
        return self.lines.select(rows=delete_idx)


def delete_digit_only_pages(text: list[str]) -> Text_Lines:
    extractor = Extractor(text)
    lines_digits: Text_Lines = extractor.get_digit_only_lines()
    lines_to_delete: Text_Lines = Line_Selector(lines_digits, max_line=10).select_lines_to_delete()
    return Text_Lines(text) - lines_to_delete


# testing
def delete_ill_ordered_pages(text: list[str]) -> Text_Lines:
    extractor = Extractor(text)
    lines_ill: Text_Lines = extractor.get_unexpected_front_matter_pages()
    lines_to_delete: Text_Lines = Line_Selector(lines_ill, max_line=10).select_lines_to_delete()
    return Text_Lines(text) - lines_to_delete


def delete_all_suspicious_pages(text: list[str]) -> Text_Lines:
    extractor = Extractor(text)
    lines_suspicous: Text_Lines = extractor.get_ill_ordered_pages() + extractor.get_digit_only_lines()
    lines_to_delete: Text_Lines = Line_Selector(lines_suspicous, max_line=10).select_lines_to_delete()
    return Text_Lines(text) - lines_to_delete


# testing
def test(text: list[str]) -> Text_Lines:
    e = Extractor(text)
    lines_cand: Text_Lines = (
        e.get_unexpected_front_matter_pages() + e.get_digit_only_lines() + e.get_non_numbered_pages()
    )
    ls = Line_Selector(lines_cand, max_line=10)
    lines_to_delete: Text_Lines = ls.select_lines_to_delete()
    print("delete these lines")
    lines_to_delete.print()
    return Text_Lines(text) - lines_to_delete


def main():
    with open("./MCSM_clean.txt") as f:
        text = f.read()
        res: Text_Lines = test(text.split("\n"))
        print("cleaned lines")
        res.print()


if __name__ == "__main__":
    main()
