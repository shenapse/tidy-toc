from __future__ import print_function

from Cleaner import Cleaner, Interactive_Cleaner
from Extractor import Extractor
from Filter_Lines import Filter_Lines
from Filtering_Prompt import Prompt
from Interpreter import Interpreter
from Merger import Merger
from Text_Lines import Paged_Text_Lines
from Type_Alias import Path, Save_Result


def save_text(
    text: str,
    dir_out: Path,
    name_out: str,
) -> Save_Result:
    if not dir_out.exists():
        dir_out.mkdir(parents=True)
    text_path: Path = dir_out / name_out
    with open(text_path, mode="w") as tf:
        tf.write(text)
    return text_path, text_path.exists()


def get_new_file_name(file: Path, prefix: str = "", suffix: str = "", join_with: str = "") -> str:
    return f"{join_with.join([prefix,file.stem,suffix])}{file.suffix}"


def apply_clean(ptls: Paged_Text_Lines, clean_dust: bool = True) -> Paged_Text_Lines:
    if clean_dust:
        c = Cleaner()
        c.read_lines(ptls)
        ptls = c.remove_dusts()
        ic = Interactive_Cleaner(cleaner=c, lines=ptls)
        ptls = ic.remove_small_dust()
    return ptls.format_space()


def apply_select(ptls: Paged_Text_Lines, select_line: bool = True, max_line: int = 10) -> Paged_Text_Lines:
    if select_line:
        ex = Extractor(text=ptls)
        ptls_ex: Paged_Text_Lines = (
            ex.get_lines_with_unexpected_header()
            + ex.get_lines_with_unexpected_roman_number()
            + ex.get_lines_of_text_length_one()
            + ex.get_lines_with()
        )
        inter = Interpreter(range_size=max_line)
        prompt = Prompt()
        filter = Filter_Lines(ptls_ex, max_line=max_line)
        ptls = (ptls - filter.get_filtered_lines(inter, prompt)).remove_blank_rows()
    return ptls


def apply_merge(ptls: Paged_Text_Lines, merge_line: bool) -> Paged_Text_Lines:
    if merge_line:
        mer = Merger(ptls)
        ptls = mer.get_merged_lines()
    return ptls


def tidy(
    text_file: Path | str,
    clean_dust: bool = True,
    select_line: bool = True,
    merge_line: bool = True,
    max_line: int = 10,
    dir: Path | str | None = None,
    prefix: str = "",
    suffix: str = "_cleaned",
    join_with: str = "",
    overwrite: bool = False,
) -> Path:
    file: Path = Path(text_file)
    with open(str(file)) as f:
        # get cleaned text
        text: str = f.read()
        ptls = Paged_Text_Lines(text)
        assert isinstance(ptls, Paged_Text_Lines)
        ptls = apply_clean(ptls, clean_dust=clean_dust)
        ptls = apply_select(ptls, select_line=select_line, max_line=max_line)
        ptls = apply_merge(ptls, merge_line=merge_line)
        text_processed: str = ptls.to_text()
        # saving procedure
        dir_out: Path = file.parent if dir is None else Path(dir)
        saved_file, success = save_text(
            text=text_processed,
            dir_out=file.parent if overwrite else dir_out,
            name_out=file.name
            if overwrite
            else get_new_file_name(file=file, prefix=prefix, suffix=suffix, join_with=join_with),
        )
        if not success:
            raise Exception(f"failed to save {str(saved_file)}.")
        return saved_file


if __name__ == "__main__":
    file = "./sample/MCSM_cleaned.txt"
    with open(file) as f:
        text = f.read()
        ptls = Paged_Text_Lines(text)
        ptls = apply_clean(ptls=ptls)
        ptls = apply_select(ptls)
        ptls = apply_merge(ptls=ptls, merge_line=True)
