"""CLI 入口:python -m seo_demo.run --keyword "industrial gearbox motor" --mode mock"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import yaml

from .graph import build_graph
from .mock_llm import MockLLM
from .models import BrandProfile
from .nodes import set_llm

DEFAULT_PROFILE = Path(__file__).resolve().parents[2] / "config" / "prompt_profile.example.yaml"


def _load_profile(path: Path) -> BrandProfile:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    kb = raw.get("company_kb", {})
    return BrandProfile(
        brand_voice=raw.get("brand_voice", "neutral"),
        positioning=kb.get("positioning", ""),
        differentiators=kb.get("differentiators", []),
        forbidden_claims=kb.get("forbidden_claims", []),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="SEO content workflow demo")
    parser.add_argument("--keyword", required=True)
    parser.add_argument("--mode", choices=["mock", "preview", "publish"], default="mock")
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--out", type=Path, default=Path("artifacts"))
    args = parser.parse_args()

    if args.mode != "mock":
        print("[demo] 本仓库只内置 mock 模式;preview/publish 需要接入真实 SERP/LLM 客户端。")
        print("[demo] 继续以 mock 模式运行,展示完整流水线。\n")

    set_llm(MockLLM())
    profile = _load_profile(args.profile)

    slug = re.sub(r"[^a-z0-9]+", "_", args.keyword.lower()).strip("_")[:24]
    run_id = f"{datetime.now():%Y%m%d_%H%M%S}_{slug}"
    run_dir = args.out / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    final = build_graph().invoke(
        {
            "keyword": args.keyword,
            "run_mode": "mock",
            "profile": profile.model_dump(),
            "errors": [],
        }
    )

    if final.get("errors"):
        for err in final["errors"]:
            (run_dir / f"error_{err['stage']}.txt").write_text(err["raw"], encoding="utf-8")
            print(f"[FAILED] stage={err['stage']}  原始输出已保留: error_{err['stage']}.txt")
        return 1

    outputs = {
        "01_serp.json": json.dumps(final["serp"], ensure_ascii=False, indent=2),
        "02_outline.json": json.dumps(final["outline"], ensure_ascii=False, indent=2),
        "03_draft.md": final["draft"],
        "04_brand_draft.md": final["brand_draft"],
        "05_audit.json": json.dumps(final["audit"], ensure_ascii=False, indent=2),
        "06_publish_payload.json": json.dumps(final["publish_payload"], ensure_ascii=False, indent=2),
    }
    for name, content in outputs.items():
        (run_dir / name).write_text(content, encoding="utf-8")

    passed = final["audit"]["passed"]
    print(f"run_id : {run_id}")
    print(f"keyword: {args.keyword}")
    print(f"audit  : {'PASSED' if passed else 'BLOCKED (需人工处理)'}")
    print(f"payload: title={final['publish_payload']['title']!r} slug={final['publish_payload']['slug']!r}")
    print(f"artifacts -> {run_dir}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
