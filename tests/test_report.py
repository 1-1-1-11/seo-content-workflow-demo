import importlib
import json
from pathlib import Path

import gen_report


def _write_run(run_dir: Path, keyword: str = "industrial gearbox motor") -> None:
    run_dir.mkdir(parents=True)
    (run_dir / "01_serp.json").write_text(
        json.dumps(
            {
                "keyword": keyword,
                "competitor_titles": ["Top 10"],
                "paa_questions": ["What is it?"],
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "02_outline.json").write_text(
        json.dumps({"sections": [{"h2": "Specs", "intent": "commercial"}]}),
        encoding="utf-8",
    )
    (run_dir / "04_brand_draft.md").write_text("# Title\n\nHello\n", encoding="utf-8")
    (run_dir / "05_audit.json").write_text(
        json.dumps({"passed": True, "checks": [{"name": "has_h1", "ok": True, "detail": "found 1 H1"}]}),
        encoding="utf-8",
    )


def test_import_does_not_touch_artifacts(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    importlib.reload(gen_report)
    assert not (tmp_path / "artifacts").exists()


def test_missing_artifacts_exit_cleanly(tmp_path, capsys):
    out = tmp_path / "report.html"
    code = gen_report.main(["--artifacts", str(tmp_path / "missing"), "--out", str(out)])
    assert code == 1
    assert not out.exists()
    assert "Traceback" not in capsys.readouterr().err


def test_report_escapes_keyword_and_skips_incomplete_runs(tmp_path):
    incomplete = tmp_path / "zzz_newer"
    incomplete.mkdir()
    (incomplete / "note.txt").write_text("skip", encoding="utf-8")
    keyword = "<script>alert(1)</script>"
    run_dir = tmp_path / "20200101_000000_demo"
    _write_run(run_dir, keyword)
    (run_dir / "06_publish_payload.json").write_text(
        json.dumps({"title": "T", "slug": "t", "status": "draft", "meta_description": "Intro"}),
        encoding="utf-8",
    )
    out = tmp_path / "report.html"
    assert gen_report.main(["--artifacts", str(tmp_path), "--out", str(out)]) == 0
    page = out.read_text(encoding="utf-8")
    assert "<script>" not in page
    assert "&lt;script&gt;" in page
    assert "zzz_newer" not in page


def test_blocked_run_renders_without_payload(tmp_path):
    run_dir = tmp_path / "20200101_000000_blocked"
    _write_run(run_dir)
    page = gen_report.render_report(run_dir)
    assert "未生成" in page
    assert "审核通过" in page
