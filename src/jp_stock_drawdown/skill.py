from __future__ import annotations

import os
from importlib.resources import files

from jp_stock_drawdown.errors import JpStockDrawdownError

SKILL_NAME = "jp-stock-drawdown"
DEFAULT_DIR = "~/.config/opencode/skills"


def read_packaged_skill() -> str:
    resource = files("jp_stock_drawdown").joinpath("data", "skill", "SKILL.md")
    return resource.read_text(encoding="utf-8")


_BLOCK_SCALAR_INDICATORS = {">", ">-", ">+", "|", "|-", "|+"}


def parse_frontmatter(content: str) -> dict:
    if not content.startswith("---"):
        raise JpStockDrawdownError("skill file has no frontmatter")
    meta: dict = {}
    key: str | None = None
    block_lines: list[str] | None = None
    for raw in content.splitlines()[1:]:
        if raw.strip() == "---":
            break
        indented = raw[:1] in (" ", "\t")
        if block_lines is not None:
            if indented or raw.strip() == "":
                block_lines.append(raw.strip())
                continue
            meta[key] = " ".join(block_lines)
            block_lines = None
            key = None
        if indented and key:
            meta[key] = meta[key] + " " + raw.strip()
            continue
        if ":" in raw:
            k, _, v = raw.partition(":")
            key = k.strip()
            value = v.strip()
            if value in _BLOCK_SCALAR_INDICATORS:
                block_lines = []
                continue
            meta[key] = value
    if block_lines is not None and key is not None:
        meta[key] = " ".join(block_lines)
    return meta


def validate_frontmatter(content: str) -> dict:
    meta = parse_frontmatter(content)
    if meta.get("name") != SKILL_NAME:
        raise JpStockDrawdownError(f"skill frontmatter 'name' must be '{SKILL_NAME}'")
    if not meta.get("description"):
        raise JpStockDrawdownError("skill frontmatter 'description' is required")
    return meta


def install_skill(target_dir: str | None = None, force: bool = False) -> str:
    content = read_packaged_skill()
    validate_frontmatter(content)
    base = os.path.expanduser(target_dir or DEFAULT_DIR)
    dest_dir = os.path.join(base, SKILL_NAME)
    dest = os.path.join(dest_dir, "SKILL.md")
    if os.path.exists(dest) and not force:
        raise JpStockDrawdownError(f"skill already installed at {dest} (use --force to overwrite)")
    os.makedirs(dest_dir, exist_ok=True)
    with open(dest, "w", encoding="utf-8") as handle:
        handle.write(content)
    return dest
