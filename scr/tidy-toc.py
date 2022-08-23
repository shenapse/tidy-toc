import click

from main import tidy

# this file is for turning main.py into command line tool by click package.
# just decorating core functions in main.py


@click.command(help="clean OCRed ToC text data.")
@click.argument("text_file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "-c",
    "--clean",
    type=bool,
    is_flag=True,
    help="remove useless characters such as the long series of periods between text and page number, e.g., 'Introduction [.........,..,,.,..] 1'",
)
@click.option(
    "-s",
    "--select",
    type=bool,
    is_flag=True,
    help="suggest unnecessary rows, such as 'xii', 'iv Contents', and ask user to select from them interactively.",
)
@click.option(
    "-m",
    "--merge",
    type=bool,
    is_flag=True,
    help="suggest neighboring two rows that might be originally in a same row, such as '1.1 hello' followed by 'world 5.'",
)
@click.option(
    "-p",
    "--page",
    type=bool,
    is_flag=True,
    help="point out badly page-numbered rows and correct them interactively.",
)
@click.option(
    "-l",
    "--maxline",
    type=int,
    default=10,
    help="the number of suggested rows displayed at once in the --select process. the default uses 10. will be ignored unless --select option is enabled.",
)
@click.option(
    "-d",
    "--dirout",
    type=click.Path(file_okay=False),
    help="directory where output text file is saved. the default uses the same place as the input text file.",
)
@click.option(
    "--pre",
    default="",
    type=str,
    help="prefix for the stem-name of the output text file. the default is ''. see --join option.",
)
@click.option(
    "--suf",
    default="_cleaned",
    type=str,
    help="suffix for the stem-name of the output text file. the default is '_cleaned'. see --join option.",
)
@click.option(
    "-j",
    "--join",
    default="",
    type=str,
    help="the character with which prefix + (text file name) + suffix are combined. e.g., prefix='pre', text file name='sample.txt', suffix='suf', join='_' -> output text file name='pre_sample_suf.txt'",
)
@click.option(
    "-o",
    "--overwrite",
    type=bool,
    is_flag=True,
    help="overwrite input file with output. If enabled, all options for output file name such as --pre and --join are ignored.",
)
def tidy_toc(
    text_file: str,
    clean: bool,
    select: bool,
    merge: bool,
    page: bool,
    maxline: int,
    dirout: str | None,
    pre: str,
    suf: str,
    join: str,
    overwrite: bool,
) -> None:
    tidy(
        text_file=text_file,
        clean_dust=clean,
        select_line=select,
        merge_line=merge,
        correct_page_number=page,
        max_line=maxline,
        dir=dirout,
        prefix=pre,
        suffix=suf,
        join_with=join,
        overwrite=overwrite,
    )


if __name__ == "__main__":
    tidy_toc()
