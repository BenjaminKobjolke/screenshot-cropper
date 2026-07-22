"""
Unit tests for the recent-projects store.
"""
from __future__ import annotations

import json

from src.editor.recents import MAX_RECENT, RecentProjects


def _store(tmp_path) -> RecentProjects:
    return RecentProjects(str(tmp_path / "recents.json"))


def _project_dir(tmp_path, name: str) -> str:
    d = tmp_path / name
    d.mkdir()
    (d / "screenshot-cropper.json").write_text("{}", encoding="utf-8")
    return str(d)


def test_load_missing_file_is_empty(tmp_path):
    assert _store(tmp_path).load() == []


def test_add_persists_and_orders_most_recent_first(tmp_path):
    store = _store(tmp_path)
    a = _project_dir(tmp_path, "a")
    b = _project_dir(tmp_path, "b")
    store.add(a)
    store.add(b)
    assert _store(tmp_path).load() == [b, a]


def test_add_dedupes_and_moves_to_front(tmp_path):
    store = _store(tmp_path)
    a = _project_dir(tmp_path, "a")
    b = _project_dir(tmp_path, "b")
    store.add(a)
    store.add(b)
    store.add(a)
    assert store.load() == [a, b]


def test_capped_at_max(tmp_path):
    store = _store(tmp_path)
    dirs = [_project_dir(tmp_path, f"p{i}") for i in range(MAX_RECENT + 3)]
    for d in dirs:
        store.add(d)
    loaded = store.load()
    assert len(loaded) == MAX_RECENT
    assert loaded[0] == dirs[-1]


def test_load_skips_projects_without_config(tmp_path):
    store = _store(tmp_path)
    a = _project_dir(tmp_path, "a")
    gone = tmp_path / "gone"
    gone.mkdir()
    (gone / "screenshot-cropper.json").write_text("{}", encoding="utf-8")
    store.add(a)
    store.add(str(gone))
    (gone / "screenshot-cropper.json").unlink()
    assert store.load() == [a]


def test_load_survives_corrupt_file(tmp_path):
    path = tmp_path / "recents.json"
    path.write_text("not json", encoding="utf-8")
    assert RecentProjects(str(path)).load() == []


def test_stored_file_is_plain_json_list(tmp_path):
    store = _store(tmp_path)
    a = _project_dir(tmp_path, "a")
    store.add(a)
    raw = json.loads((tmp_path / "recents.json").read_text(encoding="utf-8"))
    assert raw == [a]
