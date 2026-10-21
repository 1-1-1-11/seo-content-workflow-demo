"""CLI 入口: python -m seo_demo.run --keyword "industrial gearbox motor" --mode mock"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from .dotenv import load_dotenv
from .graph import build_graph
from .mock_llm import MockLLM
from .models import BrandProfile
from .nodes import set_llm
from .profile import ProfileError, discover_profile_path, load_profile
from .textutil import slugify

_STAGE = re.compile(r"[^A-Za-z0-9_-]+")


def allocate_run_dir(out: Path, run_id: str) -> Path:
    """同一秒重跑时换一个目录，避免覆盖上一次产物。"""
    out.mkdir(parents=True, exist_ok=True)
    candidate = out / run_id
    if not candidate.exists():
        candidate.mkdir()
        return candidate
    number = 2
    while True:
        alt = out / f"{run_id}_{number}"
        if not alt.exists():
            alt.mkdir()
            return alt
        number += 1


def _safe_stage(stage: str) -> str:
    cleaned = _STAGE.sub("_", stage).strip("_")
    return cleaned or "unknown"


def _write_outputs(run_dir: Path, final: dict) -> None:
    json_files = (
        ("01_serp.json", "serp"),
        ("02_outline.json", "outline"),
        ("05_audit.json", "audit"),
        ("06_publish_payload.json", "publish_payload"),
    )
    for name, key in json_files:
        if key in final:
            content = json.dumps(final[key], ensure_ascii=False, indent=2)
            (run_dir / name).write_text(content, encoding="utf-8")
    for name, key in (("03_draft.md", "draft"), ("04_brand_draft.md", "brand_draft")):
        if key in final:
            (run_dir / name).write_text(final[key], encoding="utf-8")
    for err in final.get("errors") or []:
        stage = _safe_stage(str(err.get("stage", "unknown")))
        (run_dir / f"error_{stage}.txt").write_text(str(err.get("raw", "")), encoding="utf-8")


def run_pipeline(
    *,
    keyword: str,
    profile: BrandProfile,
    out: Path,
    llm=None,
    run_mode: str = "mock",
) -> tuple[int, Path]:
    """跑通流水线并落盘。审核未过或上游失败时返回 1，但已完成的阶段仍会保留。"""
    set_llm(llm or MockLLM())
    try:
        slug = slugify(keyword, sep="_", max_len=24)
        run_id = f"{datetime.now():%Y%m%d_%H%M%S}_{slug}"
        run_dir = allocate_run_dir(out, run_id)
        final = build_graph().invoke(
            {
                "keyword": keyword,
                "run_mode": run_mode,
                "profile": profile.model_dump(),
                "errors": [],
            }
        )
        _write_outputs(run_dir, final)
    finally:
        set_llm(MockLLM())

    errors = final.get("errors") or []
    print(f"run_id : {run_dir.name}")
    print(f"keyword: {keyword}")
    if "audit" in final:
        passed = bool(final["audit"]["passed"])
        print(f"audit  : {'PASSED' if passed else 'BLOCKED (需人工处理)'}")
    if "publish_payload" in final:
        payload = final["publish_payload"]
        print(f"payload: title={payload['title']!r} slug={payload['slug']!r}")
    for err in errors:
        stage = _safe_stage(str(err.get("stage", "unknown")))
        print(f"[FAILED] stage={err.get('stage')}  原始输出已保留: error_{stage}.txt")
    print(f"artifacts -> {run_dir}/")
    blocked = "audit" in final and not final["audit"]["passed"]
    return (1 if errors or blocked else 0), run_dir


def _resolve_profile(explicit: Path | None) -> Path | None:
    if explicit is not None:
        return explicit
    env_profile = os.environ.get("SEO_DEMO_PROFILE")
    if env_profile:
        return Path(env_profile)
    return discover_profile_path()


def main(argv: list[str] | None = None) -> int:
    env_file = Path(os.environ.get("SEO_DEMO_ENV_FILE", Path.cwd() / ".env"))
    load_dotenv(env_file)

    parser = argparse.ArgumentParser(description="SEO content workflow demo")
    parser.add_argument("--keyword", default=os.environ.get("SEO_DEMO_KEYWORD"))
    parser.add_argument(
        "--mode",
        choices=["mock", "preview", "publish"],
        default=os.environ.get("SEO_DEMO_MODE", "mock"),
    )
    parser.add_argument("--profile", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    keyword = (args.keyword or "").strip()
    if not keyword:
        print("需要关键词：传入 --keyword，或设置 SEO_DEMO_KEYWORD。", file=sys.stderr)
        return 2

    if args.mode != "mock":
        print(
            "[demo] 本仓库只内置 mock 模式；preview/publish 不会访问外部 API 或 CMS。",
            file=sys.stderr,
        )
        print("[demo] 继续以 mock 生成草稿，发布载荷的 status 保持 draft。", file=sys.stderr)

    profile_path = _resolve_profile(args.profile)
    if profile_path is None:
        print(
            "[demo] 没有找到品牌配置。请传入 --profile，或设置 SEO_DEMO_PROFILE。",
            file=sys.stderr,
        )
        return 2
    try:
        profile = load_profile(profile_path)
    except ProfileError as exc:
        print(f"[demo] {exc}", file=sys.stderr)
        return 2

    out = args.out if args.out is not None else Path(os.environ.get("SEO_DEMO_OUT", "artifacts"))
    code, _run_dir = run_pipeline(
        keyword=keyword,
        profile=profile,
        out=out,
        llm=MockLLM(),
        run_mode="mock",
    )
    return code


if __name__ == "__main__":
    sys.exit(main())
