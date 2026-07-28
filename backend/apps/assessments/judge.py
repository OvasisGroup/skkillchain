"""
Subprocess-based judge for coding-exercise submissions.

*** SECURITY LIMITATION — READ BEFORE RELYING ON THIS IN PRODUCTION ***
This runs submitted source as a real `python3` subprocess on the same host
as the application, bounded only by:
  - a wall-clock timeout (subprocess.run(timeout=...)) — this is the one
    limit that's actually reliable across platforms
  - CPU time and address-space limits via `resource.setrlimit` (POSIX
    only, and even then best-effort — RLIMIT_AS in particular does not
    reliably enforce on macOS; this is written for Linux containers,
    the real deployment target)
  - stdout/stderr truncation to keep results bounded

It does NOT provide filesystem or network isolation. A submission can still
read any file the host OS user can read, or open a socket — `resource`
limits bound CPU/memory, not syscall surface. That requires a real
sandbox: a locked-down container (gVisor/Kata), a Firecracker microVM, or
a hosted judge API (e.g. Judge0) that already solved this. This module is
good enough for local development and for grading *correctness* of
cooperative student code; it is NOT sufficient isolation for untrusted
code in a real production deployment, and must not be treated as one
without a genuine threat-model review — see the M5 milestone doc's
security checklist.
"""

import resource
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

_MAX_OUTPUT_CHARS = 65536


@dataclass
class JudgeRunResult:
    stdout: str
    stderr: str
    timed_out: bool
    runtime_ms: int
    exit_code: int | None


def _limit_resources(memory_mb: int):
    def _apply():
        # Each limit is set independently and best-effort: RLIMIT_AS is
        # known to be unreliable on macOS (XNU raises "current limit
        # exceeds maximum limit" even lowering from RLIM_INFINITY — a
        # platform quirk, not something this code controls). The actual
        # deployment target is Linux containers, where this works as
        # expected; on a platform where a given limit can't be set, the
        # submission simply runs without that particular bound rather
        # than crashing the whole judge.
        mem_bytes = memory_mb * 1024 * 1024
        try:
            resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
        except (OSError, ValueError):
            pass
        try:
            # Belt-and-suspenders alongside the wall-clock timeout below —
            # bounds CPU seconds actually consumed, not wall-clock time.
            resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
        except (OSError, ValueError):
            pass

    return _apply


def run_python(
    source_code: str, stdin_input: str, *, time_limit_ms: int, memory_limit_mb: int
) -> JudgeRunResult:
    with tempfile.TemporaryDirectory() as tmp_dir:
        script_path = Path(tmp_dir) / "submission.py"
        script_path.write_text(source_code)

        started = time.monotonic()
        try:
            proc = subprocess.run(
                ["python3", str(script_path)],
                input=stdin_input,
                capture_output=True,
                text=True,
                timeout=max(time_limit_ms, 1) / 1000,
                preexec_fn=_limit_resources(memory_limit_mb),
            )
            runtime_ms = int((time.monotonic() - started) * 1000)
            return JudgeRunResult(
                stdout=proc.stdout[:_MAX_OUTPUT_CHARS],
                stderr=proc.stderr[:_MAX_OUTPUT_CHARS],
                timed_out=False,
                runtime_ms=runtime_ms,
                exit_code=proc.returncode,
            )
        except subprocess.TimeoutExpired as exc:
            runtime_ms = int((time.monotonic() - started) * 1000)
            # text=True guarantees str at runtime; TimeoutExpired's stubs
            # still type stdout/stderr as bytes | None since the generic
            # Popen signature allows binary mode too.
            timeout_stdout = exc.stdout if isinstance(exc.stdout, str) else ""
            timeout_stderr = exc.stderr if isinstance(exc.stderr, str) else ""
            return JudgeRunResult(
                stdout=timeout_stdout[:_MAX_OUTPUT_CHARS],
                stderr=timeout_stderr[:_MAX_OUTPUT_CHARS],
                timed_out=True,
                runtime_ms=runtime_ms,
                exit_code=None,
            )


def grade_submission(
    source_code: str, test_cases, *, time_limit_ms: int, memory_limit_mb: int
) -> dict:
    """
    Runs `source_code` once per test case and compares stdout (stripped)
    against each case's expected_output. Returns a dict with the overall
    weighted score/status and a per-test-case result list — the caller
    decides how much of that detail to persist/expose.
    """
    results = []
    total_weight = 0
    earned_weight = 0
    max_runtime_ms = 0
    had_error = False

    for case in test_cases:
        total_weight += case.weight
        run = run_python(
            source_code, case.input, time_limit_ms=time_limit_ms, memory_limit_mb=memory_limit_mb
        )
        max_runtime_ms = max(max_runtime_ms, run.runtime_ms)

        if run.timed_out:
            passed = False
        elif run.exit_code != 0:
            passed = False
            had_error = True
        else:
            passed = run.stdout.strip() == case.expected_output.strip()

        if passed:
            earned_weight += case.weight

        results.append(
            {
                "test_case_id": str(case.id),
                "is_hidden": case.is_hidden,
                "passed": passed,
                "timed_out": run.timed_out,
                # Only the non-hidden test cases carry the actual output
                # back — a hidden test's expected_output must never be
                # inferable from the response.
                "stdout": run.stdout if not case.is_hidden else None,
                "stderr": run.stderr if not case.is_hidden else None,
            }
        )

    score = (earned_weight / total_weight * 100) if total_weight else 0.0
    all_passed = total_weight > 0 and earned_weight == total_weight
    status = "passed" if all_passed else ("error" if had_error and earned_weight == 0 else "failed")

    return {
        "status": status,
        "score": score,
        "runtime_ms": max_runtime_ms,
        "results": results,
    }
