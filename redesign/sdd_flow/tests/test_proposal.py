import json
import os
import subprocess
import sys
from pathlib import Path


RUNNER = Path(__file__).parents[1] / "runner.py"
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True, env=ENV).stdout


def repo(tmp_path):
    r = tmp_path / "repo"; r.mkdir(); git(r, "init", "-q", "-b", "main")
    (r / "a.txt").write_text("a\n", encoding="utf-8"); git(r, "add", "."); git(r, "commit", "-qm", "base")
    return r


def proposal(state, wt, out, *extra):
    return subprocess.run([sys.executable, str(RUNNER), str(state), "proposal", "demo", str(wt), str(out), "--base", "main", *extra], capture_output=True, text=True, env=ENV)


def test_proposal_builds_one_diff_and_leaves_no_worktree(tmp_path):
    r = repo(tmp_path); (r / "novo.txt").write_text("x\n", encoding="utf-8")
    state = tmp_path / "state.json"; out = tmp_path / "demo.diff"
    result = proposal(state, r, out)
    assert result.returncode == 0, result.stderr
    assert "novo.txt" in out.read_text(encoding="utf-8")
    assert json.loads(state.read_text())["history"][-1]["stage"] == "proposal"
    assert git(r, "worktree", "list").count("\n") == 1


def test_empty_diff_is_refused(tmp_path):
    r = repo(tmp_path); out = tmp_path / "demo.diff"
    result = proposal(tmp_path / "state.json", r, out)
    assert result.returncode != 0 and "diff vazio" in result.stderr and not out.exists()


def test_whitespace_error_blocks_the_proposal(tmp_path):
    r = repo(tmp_path); (r / "ruim.txt").write_text("linha com espaco  \n", encoding="utf-8")
    out = tmp_path / "demo.diff"
    assert proposal(tmp_path / "state.json", r, out).returncode != 0 and not out.exists()
