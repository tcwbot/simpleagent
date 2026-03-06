import os
from pathlib import Path

SCHEMA = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": (
            "Write text to a file inside the current working directory only. "
            "Supports overwrite or append modes with overwrite confirmation."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative or absolute file path to write.",
                },
                "content": {
                    "type": "string",
                    "description": "Text content to write.",
                },
                "mode": {
                    "type": "string",
                    "description": "Write mode: overwrite or append.",
                    "enum": ["overwrite", "append"],
                    "default": "overwrite",
                },
                "create_dirs": {
                    "type": "boolean",
                    "description": "Create parent directories if they do not exist.",
                    "default": False,
                },
                "confirm_overwrite": {
                    "type": "boolean",
                    "description": "Required when overwriting an existing file.",
                    "default": False,
                },
            },
            "required": ["path", "content"],
        },
    },
}


def _resolve_within_cwd(path: str):
    cwd = Path(os.getcwd()).resolve()
    target = Path(path).expanduser()
    if not target.is_absolute():
        target = cwd / target
    target = target.resolve()
    if target != cwd and cwd not in target.parents:
        return None, cwd, target
    return target, cwd, target


def execute(
    path: str,
    content: str,
    mode: str = "overwrite",
    create_dirs: bool = False,
    confirm_overwrite: bool = False,
):
    try:
        if mode not in {"overwrite", "append"}:
            return "ERROR: mode must be 'overwrite' or 'append'."

        target, cwd, resolved_target = _resolve_within_cwd(path)
        if target is None:
            return (
                "ERROR: Refusing to write outside current working directory. "
                f"cwd={cwd} target={resolved_target}"
            )

        if target.exists() and target.is_dir():
            return f"ERROR: Target path is a directory, not a file: {target}"

        if mode == "overwrite" and target.exists() and not confirm_overwrite:
            return (
                "ERROR: Overwrite blocked. Re-run with confirm_overwrite=true to overwrite existing file: "
                f"{target}"
            )

        parent = target.parent
        if not parent.exists():
            if create_dirs:
                parent.mkdir(parents=True, exist_ok=True)
            else:
                return (
                    "ERROR: Parent directory does not exist. "
                    "Re-run with create_dirs=true if this is intended."
                )

        file_mode = "w" if mode == "overwrite" else "a"
        with open(target, file_mode, encoding="utf-8") as f:
            f.write(content)

        size = len(content.encode("utf-8"))
        return f"SUCCESS: Wrote {size} bytes to {target} (mode={mode})"
    except Exception as e:
        return f"ERROR: write_file failed: {type(e).__name__} - {e}"
