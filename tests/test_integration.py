import hashlib
import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx
import pytest

from slop_decisions.dataset import load_dataset, packet_for, validate
from slop_decisions.providers import Provider, ProviderConfig
from slop_decisions.rubrics import load_rubrics
from slop_decisions.runner import run_eval


@pytest.fixture
def server():
    calls = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            calls.append((self.path, dict(self.headers), body))
            verdict = {"status": "assessed", "probability": 0.95, "reason": "visible failure path"}
            data = {
                "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(verdict)}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 20},
            }
            payload = json.dumps(data).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *_):
            pass

    http = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{http.server_port}/v1", calls
    http.shutdown()
    http.server_close()
    thread.join()


def cli(*args, cwd=None, env=None):
    return subprocess.run(
        [sys.executable, "-m", "slop_decisions", *map(str, args)],
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
        timeout=20,
    )


def test_actual_cli_http_round_trip_and_exit_code(tmp_path, server):
    url, calls = server
    (tmp_path / "a.ex").write_text("def run, do: :ok\n")
    env = {
        **os.environ,
        "OPENAI_API_KEY": "secret-cloud-key",
        "OPENROUTER_API_KEY": "secret-router-key",
    }
    env.pop("LOCAL_API_KEY", None)
    result = cli(
        "check",
        "a.ex",
        "--root",
        tmp_path,
        "--provider",
        "local",
        "--model",
        "test",
        "--base-url",
        url,
        "--dimension",
        "success_shaped_failure",
        "--format",
        "json",
        env=env,
    )
    assert result.returncode == 3, result.stdout + result.stderr
    data = json.loads(result.stdout)
    assert data["warnings"] == 1 and data["unassessed"] == 0
    assert calls[0][0] == "/v1/chat/completions"
    assert "Authorization" not in calls[0][1]
    assert "secret" not in result.stdout


def test_cli_preflight_never_calls_for_missing_files_or_overbudget(tmp_path, server):
    url, calls = server
    result = cli(
        "check",
        "absent.ex",
        "--root",
        tmp_path,
        "--model",
        "x",
        "--base-url",
        url,
        "--format",
        "json",
    )
    assert result.returncode == 2
    assert json.loads(result.stdout)["error"]
    assert calls == []


@pytest.mark.parametrize(
    "command", ["checks", "dataset", "packet", "fetch", "check", "eval", "score", "sweep"]
)
def test_cli_help_is_available_without_keys(command):
    assert cli(command, "--help").returncode == 0


def fixture_dataset(tmp_path):
    code = "def fail, do: :ok\n"
    source = {
        "id": "s",
        "repo": "owner/repo",
        "revision": "a" * 40,
        "path": "lib/a.ex",
        "sha256": hashlib.sha256(code.encode()).hexdigest(),
    }
    path = tmp_path / "owner/repo" / source["revision"] / "lib/a.ex"
    path.parent.mkdir(parents=True)
    path.write_text(code)
    target = {
        "case_id": "case",
        "source_id": "s",
        "start_line": 1,
        "end_line": 1,
        "dimension": "success_shaped_failure",
        "related": [],
        "split": "dev",
        "group_id": "owner/repo#1",
        "track": "semantic",
        "extract_fixture": False,
    }
    label = {
        "case_id": "case",
        "dimension": "success_shaped_failure",
        "label": True,
        "hard_negative": False,
        "pair_id": None,
        "split": "dev",
        "status": "candidate",
    }
    return [source], [target], [label]


def test_resume_avoids_repeat_requests_and_refuses_changed_input(tmp_path, server):
    url, calls = server
    sources, targets, labels = fixture_dataset(tmp_path / "cache")
    kwargs = dict(
        targets=targets,
        labels=labels,
        sources=sources,
        cache=tmp_path / "cache",
        rubrics=load_rubrics(),
        config=ProviderConfig(provider="local", model="x", base_url=url),
        output=tmp_path / "run",
    )
    assert run_eval(**kwargs)["assessed"] == 1
    assert len(calls) == 1
    run_eval(**kwargs, resume=True)
    assert len(calls) == 1
    with pytest.raises(ValueError, match="exists"):
        run_eval(**kwargs)
    kwargs["rubrics"]["success_shaped_failure"]["predicate"] = "Changed question"
    with pytest.raises(ValueError, match="mismatch"):
        run_eval(**kwargs, resume=True)
    assert len(calls) == 1


def test_missing_context_run_records_unknown_without_key_or_request(tmp_path, server):
    sources, targets, labels = fixture_dataset(tmp_path / "cache")
    report = run_eval(
        targets,
        labels,
        sources,
        tmp_path / "absent",
        load_rubrics(),
        ProviderConfig(provider="local", model="x"),
        tmp_path / "run",
    )
    assert report["unassessed"] == 1
    assert report["usage"] == {}


def test_source_metadata_never_reaches_model_and_tampering_fails(tmp_path):
    sources, targets, labels = fixture_dataset(tmp_path)
    targets[0]["case_id"] = "before_label_true"
    targets[0]["grading_witness"] = "SECRET_LABEL"
    packet = packet_for(targets[0], sources, tmp_path)
    assert set(packet) == {"target", "files"}
    encoded = json.dumps(packet)
    for forbidden in ("before_label_true", "SECRET_LABEL", "a" * 40, "owner/repo"):
        assert forbidden not in encoded
    (tmp_path / "owner/repo" / ("a" * 40) / "lib/a.ex").write_text("changed")
    with pytest.raises(ValueError, match="hash mismatch"):
        packet_for(targets[0], sources, tmp_path)


def test_dataset_rejects_cross_repo_split_and_nonpinned_sources(tmp_path):
    sources, targets, labels = fixture_dataset(tmp_path)
    validate(sources, targets, labels)
    targets.append(dict(targets[0], case_id="case2", split="holdout", group_id="owner/repo#2"))
    with pytest.raises(ValueError, match="leaks"):
        validate(sources, targets, labels)
    sources[0]["revision"] = "main"
    with pytest.raises(ValueError, match="full commit"):
        validate(sources, targets[:1], labels)


def test_seed_invariants_and_dimensions():
    sources, targets, labels = load_dataset()
    assert len(targets) == 20
    assert sum(r["label"] for r in labels) == 8
    assert len({r["pair_id"] for r in labels if r["pair_id"]}) == 7
    assert {t["split"] for t in targets} == {"dev"}
    assert {t["dimension"] for t in targets} <= load_rubrics().keys()


@pytest.mark.parametrize(
    "status,expected_calls", [(401, 1), (403, 1), (400, 1), (429, 2), (503, 2)]
)
def test_retry_limits_and_error_redaction(monkeypatch, status, expected_calls):
    monkeypatch.setattr("slop_decisions.providers.time.sleep", lambda _: None)
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(status, json={"error": "SECRET-KEY copied into provider message"})

    with Provider(
        ProviderConfig(provider="local", model="x", retries=1),
        transport=httpx.MockTransport(handle),
    ) as p:
        result = p.assess({}, load_rubrics()["success_shaped_failure"])
    assert result["result"]["status"] == "unassessed"
    assert len(calls) == expected_calls
    assert "SECRET" not in json.dumps(result)


@pytest.mark.parametrize(
    "answers",
    [
        [],
        [{"name": "context_sufficient", "type": "predicate", "probability": 1}] * 2,
        [
            {"name": "context_sufficient", "type": "predicate", "probability": 0.1},
            {"name": "success_shaped_failure", "type": "predicate", "probability": 0.1},
        ],
        [
            {"name": "context_sufficient", "type": "predicate", "probability": 1},
            {"name": "success_shaped_failure", "type": "refusal"},
        ],
    ],
)
def test_decision_unknowns_are_not_negative(monkeypatch, answers):
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    with Provider(
        ProviderConfig(provider="openai", model="x"),
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"answers": answers})),
    ) as p:
        result = p.assess({}, load_rubrics()["success_shaped_failure"])
    assert result["result"]["status"] == "unassessed"


def test_local_never_requires_cloud_key(monkeypatch):
    monkeypatch.delenv("LOCAL_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with Provider(ProviderConfig(provider="local", model="x")):
        pass
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        Provider(ProviderConfig(provider="openai", model="x"))


@pytest.mark.parametrize("start", [True, 1.5])
def test_manifest_rejects_noninteger_line_numbers(tmp_path, start):
    sources, targets, labels = fixture_dataset(tmp_path)
    targets[0].update(start_line=start, end_line=2)
    with pytest.raises(ValueError, match="range"):
        validate(sources, targets, labels)


def test_manifest_rejects_ambiguous_labels_and_pair_members(tmp_path):
    sources, targets, labels = fixture_dataset(tmp_path)
    labels[0]["hard_negative"] = "false"
    with pytest.raises(ValueError, match="boolean"):
        validate(sources, targets, labels)
    labels[0]["hard_negative"] = False
    labels[0]["track"] = "preference"
    with pytest.raises(ValueError, match="disagree"):
        validate(sources, targets, labels)
    labels[0]["track"] = "semantic"
    labels[0]["pair_id"] = "incomplete"
    with pytest.raises(ValueError, match="pair"):
        validate(sources, targets, labels)


@pytest.mark.parametrize("name", ["context_sufficient", "invalid name"])
def test_custom_rubric_names_cannot_collide_with_protocol(tmp_path, name):
    row = dict(load_rubrics()["success_shaped_failure"], name=name)
    path = tmp_path / "rubrics.json"
    path.write_text(json.dumps([row]))
    with pytest.raises(ValueError, match="name"):
        load_rubrics(path)


def test_run_rejects_label_target_mismatch_before_requests(tmp_path, server):
    url, calls = server
    sources, targets, labels = fixture_dataset(tmp_path / "cache")
    labels[0]["case_id"] = "different"
    with pytest.raises(ValueError, match="target"):
        run_eval(
            targets,
            labels,
            sources,
            tmp_path / "cache",
            load_rubrics(),
            ProviderConfig(provider="local", model="x", base_url=url),
            tmp_path / "run",
        )
    assert not calls
    assert not (tmp_path / "run").exists()


def test_global_json_option_survives_subcommand_defaults():
    result = cli("--format", "json", "dataset")
    assert result.returncode == 0
    assert json.loads(result.stdout)["targets"] == 20
