"""Execute the Python examples and controls without a model or external service."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CASES = Path(__file__).resolve().parents[1] / "evals" / "python"
INPUTS = CASES / "inputs"


def run_case(path, target=None):
    command = [sys.executable, str(path)]
    if target is not None:
        command.append(target)
    return subprocess.run(command, capture_output=True, text=True, timeout=20)


def mutate(tmp_path, filename, before, after):
    source = (INPUTS / filename).read_text()
    assert source.count(before) == 1, "Control must change exactly one owner operation"
    path = tmp_path / filename
    path.write_text(source.replace(before, after, 1))
    return path


def assert_passes(result):
    assert result.returncode == 0, result.stdout + result.stderr


def assert_fails_test(result, test_name):
    assert result.returncode == 1, result.stdout + result.stderr
    assert f"FAIL: {test_name}" in result.stderr, result.stdout + result.stderr


class PythonCaseTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.tmp_path = Path(directory.name)

    def test_python_case_baselines_pass(self):
        for index in range(1, 9):
            filename = f"{index:02}.py"
            with self.subTest(filename=filename):
                assert_passes(run_case(INPUTS / filename))

    def test_called_mock_accepts_unawaited_submission_but_await_contract_rejects_it(self):
        tmp_path = self.tmp_path
        before = "    await transport(message)"
        after = "    pending = transport(message)\n    pending.close()"
        weak = mutate(tmp_path, "01.py", before, after)
        strong = mutate(tmp_path, "02.py", before, after)
        assert_passes(run_case(weak))
        assert_fails_test(run_case(strong), "test_awaits_one_transport_submission")

    def test_annotation_does_not_replace_public_runtime_validation(self):
        tmp_path = self.tmp_path
        path = mutate(
            tmp_path,
            "03.py",
            '    if not isinstance(value, str):\n        raise ValueError("slug must be text")\n',
            "",
        )
        result = run_case(path, "SlugTests.test_rejects_non_text_input")
        assert result.returncode == 1, result.stdout + result.stderr
        assert "AttributeError" in result.stderr
        assert "ERROR: test_rejects_non_text_input" in result.stderr

    def test_routing_contract_survives_removing_internal_accommodation(self):
        tmp_path = self.tmp_path
        path = mutate(
            tmp_path,
            "04.py",
            '    if request is None:\n        return "/default"\n'
            "    if isinstance(request, dict):\n"
            '        request = _Request(tenant=request.get("tenant", "default"))\n',
            "",
        )
        assert_passes(run_case(path))

    def test_preseeded_persistence_accepts_noop_but_fresh_connection_rejects_it(self):
        tmp_path = self.tmp_path
        path = mutate(
            tmp_path,
            "05.py",
            "        with sqlite3.connect(self.path) as db:\n"
            '            db.execute("INSERT OR REPLACE INTO accounts VALUES (?, ?)", '
            "(account_id, name))",
            "        return None",
        )
        assert_passes(run_case(path, "AccountTests.test_saves_account"))
        assert_fails_test(
            run_case(path, "AccountTests.test_new_account_survives_reopening_database"),
            "test_new_account_survives_reopening_database",
        )

    def test_absent_record_accepts_removed_guard_but_existing_record_rejects_it(self):
        tmp_path = self.tmp_path
        path = mutate(
            tmp_path,
            "06.py",
            '    if document["owner"] != actor:\n        return False\n',
            "",
        )
        assert_passes(run_case(path, "AuthorizationTests.test_other_user_cannot_delete"))
        assert_fails_test(
            run_case(path, "AuthorizationTests.test_existing_document_requires_its_owner"),
            "test_existing_document_requires_its_owner",
        )

    def test_public_capability_inventory_is_a_discriminating_contract(self):
        tmp_path = self.tmp_path
        path = mutate(
            tmp_path,
            "07.py",
            '    return {"schedule": True, "cancel": False}',
            '    return {"schedule": False, "cancel": False}',
        )
        assert_fails_test(
            run_case(path, "PublicApiTests.test_discovery_inventory"),
            "test_discovery_inventory",
        )

    def test_injected_clock_preserves_a_real_expiry_contract(self):
        tmp_path = self.tmp_path
        path = mutate(
            tmp_path,
            "07.py",
            "    return clock() + ttl_seconds",
            "    return clock()",
        )
        assert_fails_test(
            run_case(path, "PublicApiTests.test_expiry_uses_configured_clock"),
            "test_expiry_uses_configured_clock",
        )

    def test_shared_fee_oracle_accepts_wrong_fee_but_known_amount_rejects_it(self):
        tmp_path = self.tmp_path
        path = mutate(
            tmp_path,
            "08.py",
            "    return cents + cents * 5 // 100",
            "    return cents + cents * 7 // 100",
        )
        assert_passes(run_case(path, "CheckoutTests.test_checkout_charges_five_percent_fee"))
        assert_fails_test(
            run_case(path, "CheckoutTests.test_known_fee_amount"),
            "test_known_fee_amount",
        )

    def test_review_labels_resolve_to_executable_targets(self):
        cases = json.loads((CASES / "cases.json").read_text())
        for case in cases:
            path = (CASES / case["path"]).resolve()
            assert path.is_relative_to(INPUTS.resolve())
            if ".test_" in case["target"]:
                result = run_case(path, case["target"])
                assert_passes(result)
                assert "Ran 1 test" in result.stderr


if __name__ == "__main__":
    unittest.main()
