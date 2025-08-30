import os
from pathlib import Path
import shutil
import json

import pytest

from formatv.scan import find_video_files
from formatv.execute import check_and_save_duplicates


@pytest.fixture(autouse=True)
def patch_config(monkeypatch):
    # 让测试独立于外部 config.json：
    import formatv.config as cfg
    import formatv.scan as scan_mod
    import formatv.execute as exec_mod

    prefix_list = [
        {
            "name": "hb",
            "prefix": "[#hb]",
            "description": "test hb prefix",
        }
    ]

    # 覆盖 config 层
    monkeypatch.setattr(cfg, "get_blacklist", lambda: [])
    monkeypatch.setattr(cfg, "get_prefix_list", lambda: prefix_list)

    # 覆盖 scan/execute 模块在导入时绑定的函数引用
    monkeypatch.setattr(scan_mod, "get_blacklist", lambda: [])
    monkeypatch.setattr(scan_mod, "get_prefix_list", lambda: prefix_list)
    monkeypatch.setattr(exec_mod, "get_prefix_list", lambda: prefix_list)
    yield


def write_file(path: Path, size: int):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(b"0" * size)


@pytest.fixture()
def tmp_video_dir(tmp_path: Path):
    # 目录结构:
    # /dir
    #   movie.mkv (100B)
    #   [#hb]movie.mp4 (150B)   -> 跨格式，前缀更大
    #   clip.mp4 (200B)
    #   [#hb]clip.mkv (120B)    -> 跨格式，前缀更小
    #   doc.txt (无关)
    d = tmp_path / "dir"
    d.mkdir()

    write_file(d / "movie.mkv", 100)
    write_file(d / "[#hb]movie.mp4", 150)
    write_file(d / "clip.mp4", 200)
    write_file(d / "[#hb]clip.mkv", 120)
    (d / "doc.txt").write_text("hello", encoding="utf-8")

    return d


def test_scan_prefixed_ignores_extension(tmp_video_dir: Path):
    res = find_video_files(str(tmp_video_dir))

    # prefixed 收集不再要求扩展名匹配
    hb_files = res["prefixed_files"].get("hb", [])
    assert any(Path(p).name == "[#hb]movie.mp4" for p in hb_files)
    assert any(Path(p).name == "[#hb]clip.mkv" for p in hb_files)

    # normal_files 只包含视频扩展
    normals = [Path(p).name for p in res["normal_files"]]
    assert "movie.mkv" in normals and "clip.mp4" in normals


def test_execute_pairs_and_prefixed_larger(tmp_video_dir: Path, monkeypatch):
    # 禁掉剪贴板副作用
    import formatv.execute as exec_mod
    monkeypatch.setattr(exec_mod.pyperclip, "copy", lambda _: None)

    # 构造 scan_results 的合并结构
    scan_results = find_video_files(str(tmp_video_dir))

    out = check_and_save_duplicates(str(tmp_video_dir),
                                    {"nov_files": scan_results["nov_files"],
                                     "normal_files": scan_results["normal_files"],
                                     "prefixed_files": scan_results["prefixed_files"]},
                                    prefix_name="hb")

    # 应跨格式配对两对
    assert len(out["pairs"]) == 2

    # 标记前缀更大的那一对（movie）
    larger = out["prefixed_larger"]
    names = {(Path(p).name, Path(o).name) for p, o, _, _ in larger}
    assert ("[#hb]movie.mp4", "movie.mkv") in names

    # 同目录限定：路径父目录应一致
    for p, o in [(p, o) for p, o, _, _ in larger]:
        assert Path(p).parent == Path(o).parent
