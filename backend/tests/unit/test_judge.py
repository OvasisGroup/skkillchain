import sys
from dataclasses import dataclass

import pytest

from apps.assessments import judge


@dataclass
class FakeTestCase:
    id: str
    input: str
    expected_output: str
    is_hidden: bool
    weight: int


class TestRunPython:
    def test_correct_output(self):
        result = judge.run_python("print(1 + 1)", "", time_limit_ms=2000, memory_limit_mb=256)

        assert result.exit_code == 0
        assert result.stdout.strip() == "2"
        assert result.timed_out is False

    def test_reads_stdin(self):
        result = judge.run_python(
            "n = int(input()); print(n * 2)", "21\n", time_limit_ms=2000, memory_limit_mb=256
        )

        assert result.stdout.strip() == "42"

    def test_syntax_error_is_nonzero_exit_not_a_crash(self):
        result = judge.run_python("def broken(:", "", time_limit_ms=2000, memory_limit_mb=256)

        assert result.exit_code != 0
        assert result.timed_out is False

    def test_infinite_loop_times_out(self):
        result = judge.run_python("while True: pass", "", time_limit_ms=300, memory_limit_mb=256)

        assert result.timed_out is True
        # Enforced close to the requested limit, not left running.
        assert result.runtime_ms < 3000

    @pytest.mark.skipif(
        sys.platform == "darwin",
        reason=(
            "RLIMIT_AS enforcement is unreliable on macOS (XNU kernel quirk, "
            "documented in judge.py) — this genuinely only holds on the Linux "
            "containers this judge actually ships to."
        ),
    )
    def test_memory_limit_enforced_on_linux(self):
        result = judge.run_python(
            "x = bytearray(500 * 1024 * 1024)", "", time_limit_ms=3000, memory_limit_mb=50
        )

        assert result.exit_code != 0


class TestGradeSubmission:
    def test_all_pass_scores_100(self):
        cases = [
            FakeTestCase(id="1", input="", expected_output="2", is_hidden=False, weight=1),
            FakeTestCase(id="2", input="", expected_output="2", is_hidden=True, weight=1),
        ]

        outcome = judge.grade_submission(
            "print(1 + 1)", cases, time_limit_ms=2000, memory_limit_mb=256
        )

        assert outcome["status"] == "passed"
        assert outcome["score"] == 100.0
        assert all(r["passed"] for r in outcome["results"])

    def test_weighted_partial_credit(self):
        cases = [
            FakeTestCase(id="1", input="", expected_output="2", is_hidden=False, weight=3),
            FakeTestCase(
                id="2", input="", expected_output="wrong-answer", is_hidden=False, weight=1
            ),
        ]

        outcome = judge.grade_submission(
            "print(1 + 1)", cases, time_limit_ms=2000, memory_limit_mb=256
        )

        assert outcome["status"] == "failed"
        assert outcome["score"] == 75.0  # 3/4 weight earned

    def test_hidden_test_case_never_leaks_expected_output_or_stdout(self):
        cases = [
            FakeTestCase(id="1", input="", expected_output="2", is_hidden=True, weight=1),
        ]

        outcome = judge.grade_submission(
            "print(1 + 1)", cases, time_limit_ms=2000, memory_limit_mb=256
        )

        result = outcome["results"][0]
        assert result["passed"] is True
        assert result["stdout"] is None
        assert result["stderr"] is None

    def test_visible_test_case_includes_stdout(self):
        cases = [
            FakeTestCase(id="1", input="", expected_output="2", is_hidden=False, weight=1),
        ]

        outcome = judge.grade_submission(
            "print(1 + 1)", cases, time_limit_ms=2000, memory_limit_mb=256
        )

        assert outcome["results"][0]["stdout"].strip() == "2"

    def test_crashing_submission_is_status_error_when_nothing_passes(self):
        cases = [
            FakeTestCase(id="1", input="", expected_output="anything", is_hidden=False, weight=1),
        ]

        outcome = judge.grade_submission(
            "raise ValueError('boom')", cases, time_limit_ms=2000, memory_limit_mb=256
        )

        assert outcome["status"] == "error"
        assert outcome["score"] == 0.0
