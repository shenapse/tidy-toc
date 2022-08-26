from Cleaner import Cleaner, Cleaner_ja, Interactive_Cleaner
from Extractor import Extractor
from Filter_Lines import Filter_Lines
from Filtering_Prompt import Prompt
from Interpreter import Interpreter
from Merger import Merger
from Page_Corrector import Correct, Fill
from Spacer import Insert_Space, Remove_Space
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


def apply_clean(ptls: Paged_Text_Lines, clean_dust: bool = True, ja: bool = False) -> Paged_Text_Lines:
    if clean_dust:
        c = Cleaner_ja() if ja else Cleaner()
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


def apply_page_correct(ptls: Paged_Text_Lines, correct_page: bool) -> Paged_Text_Lines:
    if correct_page:
        ex = Extractor(text=ptls)
        lines_not_numbered = ex.get_non_numbered_lines()
        filler = Fill(lines_blank_page_number=lines_not_numbered, lines_ref=ptls)
        ptls = filler.get_filled_lines()
        ex.read_text(ptls)
        cor = Correct(
            lines_strange_page_number=ex.get_order_disturbing_main_pages(),
            lines_ref=ptls,
            ignore=lines_not_numbered.get_index(),
        )
        ptls = cor.get_corrected_lines()
    return ptls


def insert_space(ptls: Paged_Text_Lines, spacing: bool) -> Paged_Text_Lines:
    if spacing:
        inserter = Insert_Space(ptls)
        ptls = inserter.get_rows_space_inserted()
        remover = Remove_Space(ptls)
        ptls = remover.get_rows_space_removed()
    return ptls


def tidy(
    text_file: Path | str,
    clean_dust: bool = True,
    select_line: bool = True,
    merge_line: bool = True,
    correct_page_number: bool = True,
    ja: bool = False,
    spacing: bool = False,
    max_line: int = 10,
    dir: Path | str | None = None,
    prefix: str = "",
    suffix: str = "_cleaned",
    join_with: str = "",
    overwrite: bool = False,
) -> Path:
    file: Path = Path(text_file)
    print(f"reading {file.name}.")
    with open(str(file)) as f:
        # get cleaned text
        text: str = f.read()
        ptls = Paged_Text_Lines(text)
        assert isinstance(ptls, Paged_Text_Lines)
        ptls = apply_clean(ptls, clean_dust=clean_dust, ja=ja)
        ptls = apply_select(ptls, select_line=select_line, max_line=max_line)
        ptls = apply_merge(ptls, merge_line=merge_line)
        ptls = apply_page_correct(ptls, correct_page_number)
        ptls = insert_space(ptls, spacing=spacing)
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


def tidy_all(
    dir: Path | str,
    clean_dust: bool = True,
    select_line: bool = True,
    merge_line: bool = True,
    correct_page_number: bool = True,
    ja: bool = False,
    spacing: bool = False,
    max_line: int = 10,
    dirout: Path | str | None = None,
    prefix: str = "",
    suffix: str = "_cleaned",
    join_with: str = "",
    overwrite: bool = False,
):
    dir = Path(dir)
    if not dir.is_dir():
        raise ValueError(f"{dir} is not a directory.")
    for file in dir.glob("*.txt"):
        tidy(
            text_file=file,
            clean_dust=clean_dust,
            select_line=select_line,
            merge_line=merge_line,
            correct_page_number=correct_page_number,
            ja=ja,
            spacing=spacing,
            max_line=max_line,
            dir=dirout,
            prefix=prefix,
            suffix=suffix,
            join_with=join_with,
            overwrite=overwrite,
        )
