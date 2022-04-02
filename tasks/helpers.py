import os
import shutil

import elastic_log_cli as package

_HEADER_LEVEL_CHARACTERS = {1: "#", 2: "=", 3: "-"}


def print_header(text: str, level: int = 1, icon: str = ""):
    icon = f" {icon} " if icon else " "

    padding_character = _HEADER_LEVEL_CHARACTERS[level]
    padding_length = max(shutil.get_terminal_size((80, 20)).columns - (len(icon) * 2), 0)
    padding = f"\n{{:{padding_character}^{padding_length}}}\n"
    if level == 1:
        text = text.upper()
    print(padding.format(f"{icon}{text}{icon}"))


def run_outside_venv(ctx, *args, **kwargs):
    environment = os.environ.copy()
    venv_path = environment.get("VIRTUAL_ENV")
    if venv_path:
        del environment["VIRTUAL_ENV"]
    environment["PATH"] = ":".join(
        [path for path in environment.get("PATH", "").split(":") if path != f"{venv_path}/bin"]
    )
    environment.update(kwargs.pop("env", {}))
    ctx.run(*args, env=environment, **kwargs)


__all__ = ["print_header", "package"]
