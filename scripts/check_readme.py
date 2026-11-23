"""Require README updates alongside implementation changes, locally and in CI."""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

IMPLEMENTATION_ROOTS = ("src/", "scripts/", "tests/", ".github/workflows/")
IMPLEMENTATION_FILES = {
    ".editorconfig",
    ".gitattributes",
    "requirements.txt",
    "manage.py",
    "AGENTS.md",
}


def git(
    repo,
    *arguments,
):
    result = subprocess.run(
        ["git", *arguments],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.splitlines()


def changed_paths(
    repo,
    base=None,
):
    event_name = os.environ.get("GITHUB_EVENT_NAME")
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    is_pull_request = False
    if (
        base is None
        and event_name in ("push", "pull_request")
        and event_path
    ):
        event = json.loads(Path(event_path).read_text(encoding="utf-8"))
        is_pull_request = event_name == "pull_request"
        base = event["pull_request"]["base"]["sha"] if is_pull_request else event.get("before")
        if not base:
            raise ValueError("The CI event did not provide a base commit.")
    if base is not None:
        if not re.fullmatch(
            r"[0-9a-fA-F]{40}",
            base,
        ):
            raise ValueError("The base must be a full Git commit SHA.")
        if set(base) == {"0"}:
            return set(
                git(
                    repo,
                    "ls-tree",
                    "--name-only",
                    "-r",
                    "HEAD",
                )
            )
        arguments = (f"{base}...HEAD",) if is_pull_request else (base, "HEAD")
        return set(
            git(
                repo,
                "diff",
                "--name-only",
                *arguments,
                "--",
            )
        )
    # Include staged, unstaged and new files during a local edit.
    return set(
        git(
            repo,
            "diff",
            "--name-only",
            "HEAD",
            "--",
        )
    ) | set(
        git(
            repo,
            "ls-files",
            "--others",
            "--exclude-standard",
        )
    )


def main(
    argv=None,
    *,
    repo_root=None,
):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base",
        help="Full base commit SHA; otherwise use the CI event or local edits.",
    )
    args = parser.parse_args(argv)
    repo = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[1]
    try:
        changed = changed_paths(
            repo,
            args.base,
        )
    except (subprocess.CalledProcessError, OSError, ValueError, KeyError) as error:
        print(
            f"README check could not determine changes: {error}",
            file=sys.stderr,
        )
        return 2
    implementation = sorted(
        path
        for path in changed
        if path in IMPLEMENTATION_FILES or path.startswith(IMPLEMENTATION_ROOTS)
    )
    if (
        implementation
        and ("README.md" not in changed or not (repo / "README.md").is_file())
    ):
        print(
            "Update README.md in the same change as these implementation files:",
            file=sys.stderr,
        )
        print(
            "\n".join(f"  {path}" for path in implementation),
            file=sys.stderr,
        )
        return 1
    print("README check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
