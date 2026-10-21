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
    assert final["audit"]["checks"][1]["detail"] == "found 1 H1, need exactly 1"
    meta = final["publish_payload"]["meta_description"]
    assert meta.startswith("Selecting the right equipment")
    assert "Why buyers" not in meta
    assert not meta.startswith(">")
    assert "**" not in meta
    assert final["publish_payload"]["status"] == "draft"
    assert final["publish_payload"]["slug"] == (
        "industrial-gearbox-motor-specifications-selection-buying-guide"
    )


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


def _long_draft(body: str) -> str:
    return "# Guide\n\n## A\n\n## B\n\n## C\n\n## D\n\n" + body + "\n" + ("y" * 800)


def test_two_h1s_fail_audit():
    state = {"profile": PROFILE, "brand_draft": "# One\n\n# Two\n\n" + _long_draft("body"), "errors": []}
    result = audit(state)
    h1 = next(check for check in result["audit"]["checks"] if check["name"] == "has_h1")
    assert h1["ok"] is False
    assert result["audit"]["passed"] is False


def test_forbidden_claims_use_word_boundaries():
    clean = audit({"profile": PROFILE, "brand_draft": _long_draft("Model No.10 is unguaranteed."), "errors": []})
    assert clean["audit"]["passed"] is True
    blocked = audit({"profile": PROFILE, "brand_draft": _long_draft("We are No.1."), "errors": []})
    claim = next(check for check in blocked["audit"]["checks"] if check["name"] == "forbidden_claims")
    assert claim["ok"] is False
    assert claim["detail"] == "No.1"


def test_blank_forbidden_claim_does_not_block():
    profile = {**PROFILE, "forbidden_claims": ["", "  "]}
    result = audit({"profile": profile, "brand_draft": _long_draft("plain text"), "errors": []})
    assert result["audit"]["passed"] is True
    assert result["audit"]["checks"][0]["detail"] == "clean"


def test_publish_meta_and_slug_for_non_ascii_title():
    from seo_demo.nodes import publish_prepare

    draft = (
        "# 工业减速电机\n\n"
        "用于传送带与泵组的选型说明，先看负载再询价。\n\n"
        "## 定义\n\n## 参数\n\n## 应用\n\n## 选型\n\n"
        + ("说明" * 500)
    )
    result = publish_prepare(
        {
            "errors": [],
            "audit": {"passed": True, "checks": []},
            "brand_draft": draft,
            "profile": PROFILE,
        }
    )
    payload = result["publish_payload"]
    assert payload["slug"].startswith("kw-")
    assert payload["meta_description"].startswith("用于传送带")
    assert payload["status"] == "draft"


def test_broken_upstream_preserves_raw_output():
    """上游返回垃圾时:阶段标记失败、保留原始输出、后续阶段跳过。"""
    set_llm(BrokenLLM())
    final = _invoke()
    assert final["errors"], "should record the failure"
    assert final["errors"][0]["stage"] == "serp_research"
    assert "not-json" in final["errors"][0]["raw"]
    assert "draft" not in final  # 后续阶段未执行,不伪造结果
