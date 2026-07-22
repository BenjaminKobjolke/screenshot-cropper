"""
Unit tests for editor source discovery (screenshots + locales).
"""
from __future__ import annotations

import json

from PIL import Image

from src.editor.sources import discover_screenshots, load_locales


def _make_project(tmp_path):
    shots = tmp_path / "input" / "screenshots"
    shots.mkdir(parents=True)
    locales = tmp_path / "input" / "locales"
    locales.mkdir(parents=True)
    (locales / "en.json").write_text(json.dumps({"Text_1": "Hello"}), encoding="utf-8")
    (locales / "de.json").write_text(json.dumps({"Text_1": "Hallo"}), encoding="utf-8")
    return shots


def test_discover_screenshots_index_semantics(tmp_path):
    shots = _make_project(tmp_path)
    Image.new("RGB", (4, 4)).save(shots / "07.png")
    Image.new("RGB", (4, 4)).save(shots / "cover.png")
    (shots / "notes.txt").write_text("ignore me", encoding="utf-8")

    entries = discover_screenshots(str(tmp_path))
    by_name = {e.name: e for e in entries}
    assert set(by_name) == {"07.png", "cover.png"}
    # Numbered file: index from filename, add_one False
    assert (by_name["07.png"].text_index, by_name["07.png"].add_one) == (7, False)
    # Unnumbered file: positional fallback, add_one True
    assert by_name["cover.png"].add_one is True


def test_discover_screenshots_missing_dir(tmp_path):
    assert discover_screenshots(str(tmp_path)) == []


def test_load_locales(tmp_path):
    _make_project(tmp_path)
    handler = load_locales(str(tmp_path))
    assert handler is not None
    assert sorted(handler.get_locales()) == ["de", "en"]
    assert handler.get_text("en", 0, add_one=True) == "Hello"


def test_load_locales_missing_dir(tmp_path):
    assert load_locales(str(tmp_path)) is None
