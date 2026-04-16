#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


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


def run_git_command(args) -> str:
    try:
        result = subprocess.run(
            ["git"] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return ""


def get_script_dir() -> Path:
    return Path(__file__).resolve().parent


def find_setting_file() -> Path:
    candidates = [
        get_script_dir().parent / "setting.json",
        Path.cwd() / ".claude" / "skills" / "record-code-change" / "setting.json",
        Path.cwd() / ".agents" / "skills" / "record-code-change" / "setting.json",
    ]

    for path in candidates:
        if path.exists():
            return path

    raise FileNotFoundError(
        "未找到 setting.json，请确认文件存在于 "
        ".claude/skills/record-code-change/setting.json "
        "或 .agents/skills/record-code-change/setting.json"
    )


def load_settings() -> Dict:
    setting_path = find_setting_file()
    try:
        with setting_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"setting.json 格式错误：{e}") from e

    if not isinstance(data, dict):
        raise ValueError("setting.json 顶层必须是 JSON 对象")

    return data


def get_git_dir() -> Optional[Path]:
    git_dir = run_git_command(["rev-parse", "--git-dir"])
    if not git_dir:
        return None
    return Path(git_dir).expanduser().resolve()


def get_current_project_name() -> str:
    """
    当前项目名称：优先取当前工作目录名
    """
    try:
        cwd_name = Path.cwd().resolve().name.strip()
        if cwd_name:
            return cwd_name
    except Exception:
        pass
    return ""


def get_repo_name() -> str:
    """
    仓库名称获取顺序：
    1. Git 仓库根目录名
    2. origin 远程地址解析出的仓库名
    """
    repo_root = run_git_command(["rev-parse", "--show-toplevel"])
    if repo_root:
        name = Path(repo_root).name.strip()
        if name:
            return name

    remote_url = run_git_command(["remote", "get-url", "origin"])
    if remote_url:
        normalized = remote_url.replace("\\", "/")

        match = re.search(r"/([^/]+?)(?:\.git)?$", normalized)
        if not match:
            match = re.search(r":([^/]+?)(?:\.git)?$", remote_url)

        if match:
            name = match.group(1).strip()
            if name:
                return name

    return ""


def resolve_current_branch_name() -> str:
    """
    优先兼容 unborn branch（未提交的初始分支）场景。
    获取顺序：
    1. git symbolic-ref --quiet --short HEAD
    2. git rev-parse --abbrev-ref HEAD
    3. 直接解析 .git/HEAD
    """
    branch = run_git_command(["symbolic-ref", "--quiet", "--short", "HEAD"])
    if branch:
        return branch

    branch = run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
    if branch and branch != "HEAD":
        return branch

    git_dir = get_git_dir()
    if git_dir:
        head_file = git_dir / "HEAD"
        if head_file.exists():
            try:
                content = head_file.read_text(encoding="utf-8").strip()
                match = re.match(r"^ref:\s+refs/heads/(.+)$", content)
                if match:
                    branch_name = match.group(1).strip()
                    if branch_name:
                        return branch_name
            except Exception:
                pass

    raise RuntimeError("当前无法识别 Git 分支，请回复当前分支名后再继续。")


def resolve_project_name() -> str:
    current_project_name = get_current_project_name()
    if current_project_name:
        return sanitize_name(current_project_name)

    repo_name = get_repo_name()
    if repo_name:
        return sanitize_name(repo_name)

    raise ValueError("无法确定项目名：当前项目名称和仓库名称都无法获取")


def resolve_branch_version(settings: Dict, cli_branch_name: str = "") -> str:
    if cli_branch_name:
        return sanitize_name(cli_branch_name)

    strategy = settings.get("branch_strategy", "current_git_branch")
    stop_when_missing = bool(settings.get("stop_when_branch_missing", True))

    if strategy != "current_git_branch":
        raise ValueError("当前仅支持 branch_strategy = current_git_branch")

    try:
        return sanitize_name(resolve_current_branch_name())
    except Exception:
        if stop_when_missing:
            raise RuntimeError("当前无法识别 Git 分支，请回复当前分支名后再继续。")
        raise ValueError("无法识别 Git 分支")


def resolve_vault_root(settings: Dict) -> Path:
    vault_root = (settings.get("vault_root") or "").strip()
    if not vault_root:
        raise ValueError("setting.json 缺少 vault_root 配置")

    path = Path(vault_root).expanduser().resolve()
    if not path.exists():
        raise ValueError(f"Obsidian vault 路径不存在：{path}")

    return path


def resolve_root_folder_name(settings: Dict) -> str:
    root_folder_name = (settings.get("root_folder_name") or "").strip()
    if not root_folder_name:
        return "record-code-change"
    return sanitize_name(root_folder_name)


def resolve_cli_bin(settings: Dict) -> str:
    return (settings.get("obsidian_cli_bin") or "").strip()


def update_frontmatter_last_updated(text: str, now_str: str) -> str:
    if not text.startswith("---\n"):
        return text

    pattern = r"(?m)^last_updated:\s*.*$"
    replacement = f"last_updated: {now_str}"

    if re.search(pattern, text):
        return re.sub(pattern, replacement, text, count=1)

    end_index = text.find("\n---", 4)
    if end_index != -1:
        insert_pos = end_index
        return text[:insert_pos] + f"\nlast_updated: {now_str}" + text[insert_pos:]

    return text


def ensure_frontmatter(text: str, project: str, now_str: str) -> str:
    if text.startswith("---\n"):
        return update_frontmatter_last_updated(text, now_str)

    frontmatter = (
        f"---\n"
        f"project_name: {project}\n"
        f"last_updated: {now_str}\n"
        f"record_mode: per_project_single_file\n"
        f"---\n\n"
    )
    return frontmatter + text.lstrip()


def build_initial_file(project: str, branch_version: str, now_str: str, entry_body: str) -> str:
    return (
        f"---\n"
        f"project_name: {project}\n"
        f"last_updated: {now_str}\n"
        f"record_mode: per_project_single_file\n"
        f"---\n\n"
        f"# {branch_version}\n\n"
        f"{entry_body.strip()}\n"
    )


def insert_entry_into_branch_top(text: str, branch_version: str, entry_body: str) -> str:
    """
    规则：
    - 分支不存在：在文件末尾新增 # branch
    - 分支已存在：将新记录插入到该分支标题下方最前面
    """
    normalized_entry = entry_body.strip() + "\n"

    pattern = rf"(?ms)^# {re.escape(branch_version)}\n(.*?)(?=^# |\Z)"
    match = re.search(pattern, text)

    if not match:
        return text.rstrip() + f"\n\n# {branch_version}\n\n{normalized_entry}"

    branch_block = match.group(0)
    heading_end = branch_block.find("\n")

    if heading_end == -1:
        updated_branch_block = branch_block.rstrip() + "\n\n" + normalized_entry
    else:
        heading_part = branch_block[:heading_end + 1]
        body_part = branch_block[heading_end + 1:].lstrip("\n")

        if body_part.strip():
            updated_branch_block = (
                heading_part
                + "\n"
                + normalized_entry.strip()
                + "\n\n"
                + body_part.rstrip()
                + "\n"
            )
        else:
            updated_branch_block = heading_part + "\n" + normalized_entry

    return text[:match.start()] + updated_branch_block + text[match.end():]


def try_create_with_cli(cli_bin: str, vault_root: Path, note_rel_path: str, content: str) -> bool:
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
        [cli_exe, "new", note_rel_path, "--content", content],
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
    parser.add_argument("--content-file", required=True, help="Markdown snippet file to append")
    parser.add_argument("--title", required=True, help="Brief title within 10 chars")
    parser.add_argument("--branch-name", default="", help="Optional manual branch name override")
    args = parser.parse_args()

    try:
        settings = load_settings()
        vault_root = resolve_vault_root(settings)
        root_folder_name = resolve_root_folder_name(settings)
        project = resolve_project_name()
        branch_version = resolve_branch_version(settings, args.branch_name)
        cli_bin = resolve_cli_bin(settings)
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 2

    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M")
    title = trim_title(args.title)

    content_file = Path(args.content_file).expanduser().resolve()
    if not content_file.exists():
        print(f"[ERROR] content file not found: {content_file}", file=sys.stderr)
        return 2

    entry_body = read_text(content_file).strip()
    if not entry_body:
        print("[ERROR] content file is empty", file=sys.stderr)
        return 2

    if not entry_body.lstrip().startswith("## 【"):
        entry_body = f"## 【{now_str} {title}】\n\n{entry_body}"

    note_rel = f"{root_folder_name}/{project}.md"
    note_path = vault_root / root_folder_name / f"{project}.md"

    if note_path.exists():
        existing = read_text(note_path)
        existing = ensure_frontmatter(existing, project, now_str)
        updated = insert_entry_into_branch_top(existing, branch_version, entry_body)
        updated = ensure_frontmatter(updated, project, now_str)
        write_text(note_path, updated)
        print(str(note_path))
        return 0

    initial_text = build_initial_file(project, branch_version, now_str, entry_body)

    created_by_cli = try_create_with_cli(
        cli_bin=cli_bin,
        vault_root=vault_root,
        note_rel_path=note_rel.replace("\\", "/"),
        content=initial_text,
    )

    if created_by_cli:
        print(str(note_path))
        return 0

    write_text(note_path, initial_text)
    print(str(note_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())