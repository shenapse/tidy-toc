from Type_Alias import Path, Paths


def get_non_unique_parent_dir(files: Paths) -> Paths:
    """return the duplicated named parent directories of input files"""
    dir_ng: Paths = []
    dir_name_pool: list[str] = []
    for f in files:
        dir_f: Path = f.parent
        if dir_f.stem in dir_name_pool and dir_f not in dir_ng:
            dir_ng.append(dir_f)
        dir_name_pool.append(dir_f.stem)
    return dir_ng


def collect_zip(search_from: Path | str, dir_out: Path | str) -> Paths:
    """collect zip files in sub-directories to dir_out"""
    dir_search_from: Path = Path(search_from)
    if not dir_search_from.exists():
        raise ValueError(f"path does not exist. {search_from}")
    # recursively get zip
    zips: Paths = list(dir_search_from.glob("**/*.zip"))
    # check each file is contained in independent directory
    if (dir_ng := get_non_unique_parent_dir(zips)) != []:
        err_msg: str = "\n".join(
            [
                "zip files are not contained in distinct directories.",
                "NG:",
                "\n".join([str(d) for d in dir_ng]),
            ]
        )
        raise Exception(err_msg)
    # rename zip and move up to dir_out
    new_paths: Paths = [Path(dir_out) / f"{z.parent.stem}.zip" for z in zips]
    for i, zip in enumerate(zips):
        zip.rename(new_paths[i])
    return new_paths
