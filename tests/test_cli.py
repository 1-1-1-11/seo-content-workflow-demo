import json
from pathlib import Path

import pytest

from seo_demo.mock_llm import BrokenLLM, MockLLM
from seo_demo.profile import load_profile
from seo_demo.run import allocate_run_dir, main, run_pipeline

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "config" / "prompt_profile.example.yaml"
ENV_KEYS = (
    "SEO_DEMO_KEYWORD",
    "SEO_DEMO_MODE",
    "SEO_DEMO_PROFILE",
    "SEO_DEMO_OUT",
    "SEO_DEMO_ENV_FILE",
)


@pytest.fixture
def clean_env(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    return tmp_path


class _ClaimLLM(MockLLM):
    def _brand(self, payload: dict) -> str:
        return super()._brand(payload) + "\n\nAll units are guaranteed.\n"


def test_allocate_run_dir_does_not_overwrite(tmp_path):
    first = allocate_run_dir(tmp_path, "20260101_000000_motor")
    (first / "marker.txt").write_text("keep", encoding="utf-8")
    second = allocate_run_dir(tmp_path, "20260101_000000_motor")
    assert first != second
    assert (first / "marker.txt").read_text(encoding="utf-8") == "keep"


def test_keyword_is_required(clean_env, capsys):
    assert main([]) == 2
    assert "关键词" in capsys.readouterr().err


def test_missing_profile_exits_without_traceback(clean_env, capsys):
    code = main(["--keyword", "motor", "--profile", "missing.yaml", "--out", "out"])
    assert code == 2
    err = capsys.readouterr().err
    assert "Traceback" not in err
    assert "找不到品牌配置" in err


def test_cli_writes_draft_payload(clean_env):
    out = Path("out")
    code = main(["--keyword", "industrial gearbox motor", "--profile", str(EXAMPLE), "--out", str(out)])
    assert code == 0
    run_dir = next(out.iterdir())
    assert (run_dir / "04_brand_draft.md").is_file()
    payload = json.loads((run_dir / "06_publish_payload.json").read_text(encoding="utf-8"))
    assert payload["status"] == "draft"
    assert payload["meta_description"].startswith("Selecting the right equipment")


def test_env_and_dotenv_supply_keyword(clean_env, monkeypatch):
    out = Path("from-env")
    monkeypatch.setenv("SEO_DEMO_KEYWORD", "industrial gearbox motor")
    monkeypatch.setenv("SEO_DEMO_PROFILE", str(EXAMPLE))
    monkeypatch.setenv("SEO_DEMO_OUT", str(out))
    assert main([]) == 0
    assert any(out.iterdir())

    other = Path("from-file")
    Path(".env").write_text(
        f'SEO_DEMO_KEYWORD="industrial gearbox motor"\nSEO_DEMO_PROFILE={EXAMPLE}\n',
        encoding="utf-8",
    )
    monkeypatch.delenv("SEO_DEMO_KEYWORD")
    monkeypatch.delenv("SEO_DEMO_PROFILE")
    assert main(["--out", str(other)]) == 0
    serp = json.loads(next(other.iterdir()).joinpath("01_serp.json").read_text(encoding="utf-8"))
    assert serp["keyword"] == "industrial gearbox motor"


def test_flag_overrides_env_keyword(clean_env, monkeypatch):
    monkeypatch.setenv("SEO_DEMO_KEYWORD", "should-not-win")
    out = Path("flag")
    assert main(["--keyword", "industrial gearbox motor", "--profile", str(EXAMPLE), "--out", str(out)]) == 0
    serp = json.loads(next(out.iterdir()).joinpath("01_serp.json").read_text(encoding="utf-8"))
    assert serp["keyword"] == "industrial gearbox motor"


def test_non_ascii_keyword_gets_a_run_id(clean_env):
    out = Path("zh")
    assert main(["--keyword", "工业减速电机", "--profile", str(EXAMPLE), "--out", str(out)]) == 0
    name = next(out.iterdir()).name
    assert name[-1] != "_"
    assert "_kw_" in name


def test_preview_never_publishes(clean_env, capsys):
    out = Path("preview")
    code = main(
        ["--keyword", "industrial gearbox motor", "--mode", "preview", "--profile", str(EXAMPLE), "--out", str(out)]
    )
    assert code == 0
    err = capsys.readouterr().err
    assert "不会访问" in err
    payload = json.loads(next(out.iterdir()).joinpath("06_publish_payload.json").read_text(encoding="utf-8"))
    assert payload["status"] == "draft"


def test_blocked_audit_keeps_completed_stages(clean_env):
    code, run_dir = run_pipeline(
        keyword="industrial gearbox motor",
        profile=load_profile(EXAMPLE),
        out=Path("blocked"),
        llm=_ClaimLLM(),
    )
    assert code == 1
    assert (run_dir / "04_brand_draft.md").is_file()
    assert (run_dir / "05_audit.json").is_file()
    assert not (run_dir / "06_publish_payload.json").exists()
    assert "audit blocked" in (run_dir / "error_publish_prepare.txt").read_text(encoding="utf-8")


def test_broken_upstream_writes_raw_error(clean_env):
    code, run_dir = run_pipeline(
        keyword="industrial gearbox motor",
        profile=load_profile(EXAMPLE),
        out=Path("broken"),
        llm=BrokenLLM(),
    )
    assert code == 1
    assert "not-json" in (run_dir / "error_serp_research.txt").read_text(encoding="utf-8")
    assert not (run_dir / "03_draft.md").exists()
