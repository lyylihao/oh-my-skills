#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


INVALID_CHARS = r'[<>:"/\\|?*]'


def sanitize_name(name: str) -> str:
    name = (name or "").strip()
    name = re.sub(INVALID_CHARS, "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name or "unknown"


def trim_title(title: str, limit: int = 10) -> str:
    title = (title or "").strip()
    if not title:
        return "本次更新"
    return title[:limit]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def update_last_updated(header_text: str, now_str: str) -> str:
    pattern = r"(?m)^- 最后更新：.*$"
    replacement = f"- 最后更新：{now_str}"
    if re.search(pattern, header_text):
        return re.sub(pattern, replacement, header_text)
    return header_text


def build_header(project: str, branch_version: str, now_str: str) -> str:
    return (
        f"# {project}｜{branch_version} 变更记录\n\n"
        f"## 文档说明\n"
        f"- 项目名：{project}\n"
        f"- 分支版本：{branch_version}\n"
        f"- 记录方式：同版本持续追加\n"
        f"- 最后更新：{now_str}\n"
    )


def try_create_with_cli(cli_bin: str, vault_root: Path, note_rel_path: str, content: str) -> bool:
    """
    CLI-first best effort.
    默认兼容 notesmd-cli 风格：
      notesmd-cli create "Project/branch.md" --content "..."
    其他 obsidian cli 若参数不一致，会自动 fallback 到直接文件写入。
    """
    if not cli_bin:
        return False

    cli_exe = shutil.which(cli_bin)
    if not cli_exe:
        return False

    env = os.environ.copy()
    env.setdefault("OBSIDIAN_VAULT_ROOT", str(vault_root))

    commands = [
        [cli_exe, "create", note_rel_path, "--content", content],
        [cli_exe, "note", "create", note_rel_path, "--content", content],
    ]

    for cmd in commands:
        try:
            result = subprocess.run(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return True
        except Exception:
            pass

    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Append change log note into Obsidian vault.")
    parser.add_argument("--vault-root", required=True, help="Obsidian vault root path")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--branch-version", required=True, help="Branch version")
    parser.add_argument("--title", required=True, help="Brief title within 10 chars")
    parser.add_argument("--content-file", required=True, help="Markdown snippet file to append")
    parser.add_argument(
        "--cli-bin",
        default=os.getenv("OBSIDIAN_CLI_BIN", "notesmd-cli"),
        help="Obsidian CLI executable name, default: notesmd-cli",
    )
    args = parser.parse_args()

    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M")

    vault_root = Path(args.vault_root).expanduser().resolve()
    project = sanitize_name(args.project)
    branch_version = sanitize_name(args.branch_version)
    title = trim_title(args.title)

    content_file = Path(args.content_file).expanduser().resolve()
    if not content_file.exists():
        print(f"[ERROR] content file not found: {content_file}", file=sys.stderr)
        return 2

    entry_body = read_text(content_file).strip()
    if not entry_body:
        print("[ERROR] content file is empty", file=sys.stderr)
        return 2

    note_rel = f"{project}/{branch_version}.md"
    note_path = vault_root / project / f"{branch_version}.md"

    header = build_header(project, branch_version, now_str)

    if note_path.exists():
        existing = read_text(note_path)
        existing = update_last_updated(existing, now_str)
        final_text = existing.rstrip() + "\n\n" + entry_body + "\n"
        write_text(note_path, final_text)
        print(str(note_path))
        return 0

    initial_text = header.rstrip() + "\n\n" + entry_body + "\n"

    # CLI-first best effort for initial creation
    created_by_cli = try_create_with_cli(
        cli_bin=args.cli_bin,
        vault_root=vault_root,
        note_rel_path=note_rel.replace("\\", "/"),
        content=initial_text,
    )

    if created_by_cli:
        print(str(note_path))
        return 0

    # Fallback: direct markdown write into vault
    write_text(note_path, initial_text)
    print(str(note_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())