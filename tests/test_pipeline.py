"""全链路 mock 测试:CI 不依赖任何外部服务。"""

from __future__ import annotations

import pytest

from seo_demo.graph import build_graph
from seo_demo.mock_llm import BrokenLLM, MockLLM
from seo_demo.nodes import audit, set_llm

PROFILE = {
    "brand_voice": "technical, plain-spoken",
    "positioning": "OEM industrial motor manufacturer",
    "differentiators": ["IE3/IE4 full range", "48h quote response"],
    "forbidden_claims": ["guaranteed", "No.1"],
}


@pytest.fixture(autouse=True)
def reset_llm():
    set_llm(MockLLM())
    yield
    set_llm(MockLLM())


def _invoke(errors=None):
    return build_graph().invoke(
        {"keyword": "industrial gearbox motor", "run_mode": "mock", "profile": PROFILE, "errors": errors or []}
    )


def test_full_pipeline_produces_all_artifacts():
    final = _invoke()
    assert final["errors"] == []
    assert final["serp"]["intent"] == "commercial"
    assert len(final["outline"]["sections"]) >= 4
    assert final["draft"].startswith("# ")
    assert "IE3/IE4 full range" in final["brand_draft"]
    assert final["audit"]["passed"] is True
    assert final["publish_payload"]["status"] == "draft"


def test_forbidden_claim_is_hard_blocked():
    """营销词不是'建议不用',是写了就过不了审。"""
    state = {
        "profile": PROFILE,
        "brand_draft": "# Guide\n\n## A\n\n## B\n\n## C\n\n## D\n\n"
        + "x" * 900
        + "\nAll products are guaranteed for life.",
        "errors": [],
    }
    result = audit(state)
    assert result["audit"]["passed"] is False
    assert any(c["name"] == "forbidden_claims" and not c["ok"] for c in result["audit"]["checks"])


def test_broken_upstream_preserves_raw_output():
    """上游返回垃圾时:阶段标记失败、保留原始输出、后续阶段跳过。"""
    set_llm(BrokenLLM())
    final = _invoke()
    assert final["errors"], "should record the failure"
    assert final["errors"][0]["stage"] == "serp_research"
    assert "not-json" in final["errors"][0]["raw"]
    assert "draft" not in final  # 后续阶段未执行,不伪造结果
