from Type_Alias import Path, Save_Result


def save_text(
    text: str,
    dir_out: Path,
    name_out: Path,
) -> Save_Result:
    if not dir_out.exists():
        dir_out.mkdir(parents=True)
    text_path: Path = dir_out / f"{name_out}.txt"
    with open(text_path, mode="w") as tf:
        tf.write(text)
    return text_path, text_path.exists()
