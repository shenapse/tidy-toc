from Cleaner import Cleaner
from Extractor import Extractor
from Interpreter import Interpreter
from Prompt import Prompt
from Selector import Line_Selector
from Text_Line import Text_Lines
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


def get_filtered_textlines(
    text_lines: Text_Lines,
    clean_dust: bool = True,
    select_line: bool = True,
    max_line: int = 10,
) -> Text_Lines:
    tls: Text_Lines = text_lines
    if clean_dust:
        c = Cleaner()
        c.read_lines(text_lines)
        tls: Text_Lines = c.remove_dusts()
    if select_line:
        if tls.is_nonempty():
            ex = Extractor(text=tls)
            tls_ex = (
                ex.get_lines_with_unexpected_header()
                + ex.get_unexpected_front_matter_lines()
                + ex.get_digit_only_lines()
            )
            inter = Interpreter(range_size=max_line)
            prompt = Prompt()
            ls = Line_Selector(tls_ex, max_line=max_line)
            tls = tls - ls.select_lines_to_delete(inter, prompt)
    return tls


def tidy_toc(
    text_file: Path | str,
    clean_dust: bool = True,
    select_line: bool = True,
    max_line: int = 10,
    dir: Path | None = None,
    prefix: str = "",
    suffix: str = "_cleand",
    join_with: str = "",
) -> Path:
    file: Path = Path(text_file)
    with open(file) as f:
        # get cleaned text
        text: str = f.read()
        text_cleaned: str = get_filtered_textlines(
            text_lines=Text_Lines(text), clean_dust=clean_dust, select_line=select_line, max_line=max_line
        ).to_text()
        # saving procedure
        dir_out: Path = file.parent if dir is None else dir
        saved_file, success = save_text(
            text=text_cleaned,
            dir_out=dir_out,
            name_out=get_new_file_name(file=file, prefix=prefix, suffix=suffix, join_with=join_with),
        )
        if not success:
            raise Exception(f"failed to save {str(saved_file)}.")
        return saved_file


if __name__ == "__main__":
    tidy_toc("./sample/Algebra.txt")
