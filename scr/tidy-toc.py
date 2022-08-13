import click

from main import tidy

# this file is for turning main.py into command line tool by click package.
# just decorating core functions in main.py


@click.command()
@click.argument("text_file", type=click.Path(exists=True, dir_okay=False))
@click.option("-c", "--clean", type=bool, is_flag=True)
@click.option("-s", "--select", type=bool, is_flag=True)
@click.option("-m", "--maxline", type=int, default=10)
@click.option("-d", "--dirout", type=click.Path(file_okay=False))
@click.option("--pre", default="", type=str)
@click.option("--suf", default="_cleaned", type=str)
@click.option("-j", "--join", default="", type=str)
def tidy_toc(
    text_file: str,
    clean: bool,
    select: bool,
    maxline: int,
    dirout: str | None,
    pre: str,
    suf: str,
    join: str,
) -> None:
    tidy(
        text_file=text_file,
        clean_dust=clean,
        select_line=select,
        max_line=maxline,
        dir=dirout,
        prefix=pre,
        suffix=suf,
        join_with=join,
    )


if __name__ == "__main__":
    tidy_toc()
