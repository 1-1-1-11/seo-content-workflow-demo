"""最小 .env 读取器。不覆盖进程里已经存在的变量，也不执行文件内容。"""

from __future__ import annotations

import os
import re
from collections.abc import MutableMapping
from pathlib import Path

_KEY = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def parse_dotenv(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not _KEY.fullmatch(key):
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        values[key] = value
    return values


def load_dotenv(
    path: Path,
    environ: MutableMapping[str, str] | None = None,
    *,
    override: bool = False,
) -> dict[str, str]:
    """把文件里的键写入 environ。默认不覆盖已有值。文件不存在时什么都不做。"""
    env = os.environ if environ is None else environ
    if not path.is_file():
        return {}
    applied: dict[str, str] = {}
    for key, value in parse_dotenv(path.read_text(encoding="utf-8")).items():
        if override or key not in env:
            env[key] = value
            applied[key] = value
    return applied
