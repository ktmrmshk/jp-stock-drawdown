from __future__ import annotations

import os
import re

import pytest

from jp_stock_drawdown import cli
from jp_stock_drawdown.errors import JpStockDrawdownError
from jp_stock_drawdown.skill import (
    SKILL_NAME,
    install_skill,
    parse_frontmatter,
    read_packaged_skill,
    validate_frontmatter,
)

_JAPANESE = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uff66-\uff9f]")


class TestPackagedSkill:
    def test_ac22_frontmatter_exists(self):
        meta = parse_frontmatter(read_packaged_skill())
        assert meta["name"] == "jp-stock-drawdown"
        assert meta["description"]
        assert meta["description"].startswith("Usage guide")
        assert "Examples:" in meta["description"]
        assert ">-" not in meta["description"]

    def test_block_scalar_description(self):
        content = (
            "---\n"
            "name: jp-stock-drawdown\n"
            "description: >-\n"
            "  Line one.\n"
            "  Line two with colon: here.\n"
            "---\n"
        )
        meta = parse_frontmatter(content)
        assert meta["name"] == "jp-stock-drawdown"
        assert meta["description"] == "Line one. Line two with colon: here."

    def test_ac_s01_name_matches(self):
        meta = validate_frontmatter(read_packaged_skill())
        assert meta["name"] == SKILL_NAME

    def test_ac_s04_english_only(self):
        content = read_packaged_skill()
        assert not _JAPANESE.search(content)

    def test_ac_s03_json_interpretation(self):
        content = read_packaged_skill()
        for phrase in ("drawdown_pct", "errors[]", "as_of", "yyyy-mm-dd", "negative"):
            assert phrase in content


class TestInstall:
    def test_ac_s05_installs(self, tmp_path):
        dest = install_skill(str(tmp_path))
        expected = os.path.join(str(tmp_path), SKILL_NAME, "SKILL.md")
        assert dest == expected
        with open(dest, encoding="utf-8") as handle:
            assert handle.read() == read_packaged_skill()

    def test_ac_s06_refuses_overwrite_without_force(self, tmp_path):
        dest = install_skill(str(tmp_path))
        with open(dest, "a", encoding="utf-8") as handle:
            handle.write("\n# local modification\n")
        with open(dest, encoding="utf-8") as handle:
            modified = handle.read()
        with pytest.raises(JpStockDrawdownError):
            install_skill(str(tmp_path))
        with open(dest, encoding="utf-8") as handle:
            assert handle.read() == modified

    def test_ac_s06_force_overwrites(self, tmp_path):
        dest = install_skill(str(tmp_path))
        with open(dest, "a", encoding="utf-8") as handle:
            handle.write("\n# local modification\n")
        install_skill(str(tmp_path), force=True)
        with open(dest, encoding="utf-8") as handle:
            assert handle.read() == read_packaged_skill()
    def test_tilde_is_expanded(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        dest = install_skill("~/custom-skills")
        assert dest == os.path.join(str(tmp_path), "custom-skills", SKILL_NAME, "SKILL.md")


class TestCliInstall:
    def test_ac23_installs(self, tmp_path, capsys):
        assert cli.main(["skill", "install", "--dir", str(tmp_path)]) == 0
        out = capsys.readouterr().out
        assert f"Installed skill '{SKILL_NAME}' to" in out
        path = os.path.join(str(tmp_path), SKILL_NAME, "SKILL.md")
        assert os.path.exists(path)
        with open(path, encoding="utf-8") as handle:
            assert handle.read() == read_packaged_skill()

    def test_ac23_no_force_returns_1(self, tmp_path, capsys):
        assert cli.main(["skill", "install", "--dir", str(tmp_path)]) == 0
        assert cli.main(["skill", "install", "--dir", str(tmp_path)]) == 1
        err = capsys.readouterr().err
        assert err.startswith("error: ")

    def test_ac23_force_overwrites(self, tmp_path, capsys):
        assert cli.main(["skill", "install", "--dir", str(tmp_path)]) == 0
        assert cli.main(["skill", "install", "--dir", str(tmp_path), "--force"]) == 0
