#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
导出项目 .claude 配置快照到 Markdown 文档。

用法：
    python3 export_claude_config.py /Users/yinuo/Projects/hpr-claude-project

输出：
    <project_root>/claude_config_snapshot_YYYYMMDD_HHMMSS.md
"""

from __future__ import annotations

import hashlib
import mimetypes
import os
import sys
from datetime import datetime
from pathlib import Path

MAX_TEXT_BYTES = 200_000
TEXT_EXTENSIONS = {
    ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".conf", ".py", ".sh", ".bash", ".zsh", ".js", ".ts", ".tsx",
    ".jsx", ".css", ".scss", ".html", ".xml", ".csv"
}


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def is_text_file(path: Path) -> bool:
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return True
    mime, _ = mimetypes.guess_type(str(path))
    if mime and mime.startswith("text/"):
        return True
    try:
        with path.open("rb") as f:
            sample = f.read(4096)
        sample.decode("utf-8")
        return True
    except Exception:
        return False


def safe_read_text(path: Path, max_bytes: int = MAX_TEXT_BYTES) -> str:
    raw = path.read_bytes()
    truncated = False
    if len(raw) > max_bytes:
        raw = raw[:max_bytes]
        truncated = True
    text = raw.decode("utf-8", errors="replace")
    if truncated:
        text += "\n\n[... 文件过长，已截断 ...]\n"
    return text


def build_tree(root: Path) -> str:
    lines = []

    def _walk(current: Path, prefix: str = ""):
        children = sorted(
            current.iterdir(),
            key=lambda p: (p.is_file(), p.name.lower())
        )
        for idx, child in enumerate(children):
            is_last = idx == len(children) - 1
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{child.name}")
            if child.is_dir():
                extension = "    " if is_last else "│   "
                _walk(child, prefix + extension)

    lines.append(root.name)
    _walk(root)
    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) != 2:
        print("用法: python3 export_claude_config.py <project_root>", file=sys.stderr)
        return 1

    project_root = Path(sys.argv[1]).expanduser().resolve()
    claude_dir = project_root / ".claude"

    if not project_root.exists():
        print(f"项目根目录不存在: {project_root}", file=sys.stderr)
        return 1
    if not claude_dir.exists():
        print(f"未找到 .claude 目录: {claude_dir}", file=sys.stderr)
        return 1
    if not claude_dir.is_dir():
        print(f".claude 不是目录: {claude_dir}", file=sys.stderr)
        return 1

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = project_root / f"claude_config_snapshot_{ts}.md"

    parts = []
    parts.append(f"# Claude 配置快照\n")
    parts.append(f"- 生成时间：{datetime.now().isoformat(timespec='seconds')}")
    parts.append(f"- 项目根目录：`{project_root}`")
    parts.append(f"- Claude 目录：`{claude_dir}`\n")

    parts.append("## 目录树\n")
    parts.append("```text")
    parts.append(build_tree(claude_dir))
    parts.append("```\n")

    files = [p for p in sorted(claude_dir.rglob("*")) if p.is_file()]

    parts.append("## 文件摘要\n")
    parts.append("| 相对路径 | 大小（字节） | SHA256 | 文本文件 |")
    parts.append("|---|---:|---|---|")
    for f in files:
        rel = f.relative_to(project_root)
        size = f.stat().st_size
        sha = sha256_of_file(f)
        text_flag = "是" if is_text_file(f) else "否"
        parts.append(f"| `{rel}` | {size} | `{sha}` | {text_flag} |")
    parts.append("")

    parts.append("## 文件内容展开\n")
    for f in files:
        rel = f.relative_to(project_root)
        parts.append(f"### `{rel}`\n")
        parts.append(f"- 大小：{f.stat().st_size} 字节")
        parts.append(f"- SHA256：`{sha256_of_file(f)}`")
        if is_text_file(f):
            text = safe_read_text(f)
            parts.append("\n```text")
            parts.append(text.rstrip("\n"))
            parts.append("```\n")
        else:
            parts.append("\n> 非文本文件，未展开内容。\n")

    output_path.write_text("\n".join(parts), encoding="utf-8")
    print(f"已生成快照文件：{output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())