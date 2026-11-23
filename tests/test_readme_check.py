"""Exercise documentation enforcement against real temporary Git histories."""

import importlib.util
import io
import json
import os
import subprocess
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "readme_check",
    Path(__file__).resolve().parents[1] / "scripts/check_readme.py",
)
readme_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(readme_check)


class ReadmeCheckTests(TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory(prefix="limousine-readme-check-")
        self.addCleanup(self.directory.cleanup)
        self.repo = Path(self.directory.name)
        self.git(
            "init",
            "--quiet",
        )
        (self.repo / "README.md").write_text(
            "Initial project guide\n",
            encoding="utf-8",
        )
        (self.repo / "src").mkdir()
        (self.repo / "src/app.py").write_text(
            "value = 1\n",
            encoding="utf-8",
        )
        self.commit()

    def git(
        self,
        *args,
    ):
        return subprocess.run(
            ["git", *args],
            cwd=self.repo,
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()

    def commit(self):
        self.git(
            "add",
            ".",
        )
        self.git(
            "-c",
            "commit.gpgsign=false",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "test fixture",
        )
        return self.git(
            "rev-parse",
            "HEAD",
        )

    def check(
        self,
        args=(),
        event=None,
        event_name="push",
    ):
        with (
            patch.dict(
                os.environ,
                {"GITHUB_EVENT_NAME": "", "GITHUB_EVENT_PATH": ""},
            ),
            redirect_stdout(io.StringIO()),
            redirect_stderr(io.StringIO()),
        ):
            if event is not None:
                path = self.repo / "event.json"
                path.write_text(
                    json.dumps(event),
                    encoding="utf-8",
                )
                with patch.dict(
                    os.environ,
                    {"GITHUB_EVENT_NAME": event_name, "GITHUB_EVENT_PATH": str(path)},
                ):
                    return readme_check.main(
                        list(args),
                        repo_root=self.repo,
                    )
            return readme_check.main(
                list(args),
                repo_root=self.repo,
            )

    def test_local_code_requires_readme_in_same_change(self):
        (self.repo / "src/app.py").write_text(
            "value = 2\n",
            encoding="utf-8",
        )
        self.assertEqual(
            self.check(),
            1,
        )
        (self.repo / "README.md").write_text(
            "Explains value 2\n",
            encoding="utf-8",
        )
        self.assertEqual(
            self.check(),
            0,
        )

    def test_new_and_staged_files_are_included(self):
        (self.repo / "src/new.py").write_text(
            "new = True\n",
            encoding="utf-8",
        )
        self.assertEqual(
            self.check(),
            1,
        )
        self.git(
            "add",
            "src/new.py",
        )
        self.assertEqual(
            self.check(),
            1,
        )

    def test_clean_checkout_and_supporting_docs_pass(self):
        self.assertEqual(
            self.check(),
            0,
        )
        (self.repo / "notes.md").write_text(
            "More explanation\n",
            encoding="utf-8",
        )
        self.assertEqual(
            self.check(),
            0,
        )

    def test_push_range_includes_all_commits_in_push(self):
        base = self.git(
            "rev-parse",
            "HEAD",
        )
        (self.repo / "src/app.py").write_text(
            "value = 3\n",
            encoding="utf-8",
        )
        self.commit()
        self.assertEqual(
            self.check(event={"before": base}),
            1,
        )
        (self.repo / "README.md").write_text(
            "Explains value 3\n",
            encoding="utf-8",
        )
        self.commit()
        self.assertEqual(
            self.check(event={"before": base}),
            0,
        )

    def test_initial_push_uses_committed_tree(self):
        self.assertEqual(
            self.check(event={"before": "0" * 40}),
            0,
        )

    def test_pull_request_compares_changes_since_base(self):
        base = self.git(
            "rev-parse",
            "HEAD",
        )
        (self.repo / "src/app.py").write_text(
            "value = 5\n",
            encoding="utf-8",
        )
        self.commit()
        event = {"pull_request": {"base": {"sha": base}}}
        self.assertEqual(
            self.check(
                event=event,
                event_name="pull_request",
            ),
            1,
        )
        (self.repo / "README.md").write_text(
            "Explains value 5\n",
            encoding="utf-8",
        )
        self.commit()
        self.assertEqual(
            self.check(
                event=event,
                event_name="pull_request",
            ),
            0,
        )

    def test_invalid_base_fails_closed(self):
        self.assertEqual(
            self.check(("--base", "not-a-sha")),
            2,
        )

    def test_deleted_readme_does_not_satisfy_documentation_check(self):
        (self.repo / "src/app.py").write_text(
            "value = 4\n",
            encoding="utf-8",
        )
        (self.repo / "README.md").unlink()
        self.assertEqual(
            self.check(),
            1,
        )
