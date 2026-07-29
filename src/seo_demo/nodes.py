"""6 个阶段节点。每个节点:读状态 → 产出结构化产物 → 写回状态。

失败边界:LLM 输出解析失败时,记录 stage 与原始输出到 errors,
后续节点直接跳过——不静默降级,不伪造结果。
"""

from __future__ import annotations

import re

from pydantic import ValidationError

from .mock_llm import MockLLM
from .models import AuditReport, BrandProfile, Check, Outline, PublishPayload, SerpResult
from .state import WorkflowState

_llm = MockLLM()


def set_llm(llm) -> None:
    """注入 LLM 实现。生产环境注入 OpenAI 兼容客户端;测试注入 Mock/Broken。"""
    global _llm
    _llm = llm


def _failed(state: WorkflowState) -> bool:
    return bool(state.get("errors"))


def _record_error(state: WorkflowState, stage: str, raw: str) -> dict:
    return {"errors": state.get("errors", []) + [{"stage": stage, "raw": raw[:2000]}]}


# ---------------------------------------------------------------- nodes
def serp_research(state: WorkflowState) -> dict:
    raw = _llm.complete("serp", {"keyword": state["keyword"]})
    try:
        serp = SerpResult.model_validate_json(raw)
    except ValidationError:
        return _record_error(state, "serp_research", raw)
    return {"serp": serp.model_dump()}


def architecture(state: WorkflowState) -> dict:
    if _failed(state):
        return {}
    serp = SerpResult.model_validate(state["serp"])
    raw = _llm.complete("outline", {"keyword": state["keyword"], "paa_questions": serp.paa_questions})
    try:
        outline = Outline.model_validate_json(raw)
    except ValidationError:
        return _record_error(state, "architecture", raw)
    return {"outline": outline.model_dump()}


def write_article(state: WorkflowState) -> dict:
    if _failed(state):
        return {}
    draft = _llm.complete("draft", {"outline": state["outline"]})
    if not draft.strip().startswith("#"):
        return _record_error(state, "write_article", draft)
    return {"draft": draft}


def brand_rewrite(state: WorkflowState) -> dict:
    if _failed(state):
        return {}
    brand_draft = _llm.complete("brand", {"draft": state["draft"], "profile": state["profile"]})
    if not brand_draft.strip():
        return _record_error(state, "brand_rewrite", brand_draft)
    return {"brand_draft": brand_draft}


def audit(state: WorkflowState) -> dict:
    """纯 Python 确定性检查:forbidden_claims 是硬拦截,不是建议。"""
    if _failed(state):
        return {}
    profile = BrandProfile.model_validate(state["profile"])
    text = state["brand_draft"]
    lowered = text.lower()

    checks = [
        Check(
            name="forbidden_claims",
            ok=not any(c.lower() in lowered for c in profile.forbidden_claims),
            detail=", ".join(c for c in profile.forbidden_claims if c.lower() in lowered) or "clean",
        ),
        Check(name="has_h1", ok=text.lstrip().startswith("# "), detail="exactly one H1 required"),
        Check(
            name="min_sections",
            ok=len(re.findall(r"^## ", text, flags=re.M)) >= 4,
            detail=f"found {len(re.findall(r'^## ', text, flags=re.M))} H2 sections, need >= 4",
        ),
        Check(name="min_length", ok=len(text) >= 800, detail=f"{len(text)} chars, need >= 800"),
    ]
    report = AuditReport(passed=all(c.ok for c in checks), checks=checks)
    return {"audit": report.model_dump()}


def publish_prepare(state: WorkflowState) -> dict:
    """只生成发布载荷;真正的 WordPress 草稿创建是人工确认后的二次动作。"""
    if _failed(state):
        return {}
    audit_report = AuditReport.model_validate(state["audit"])
    if not audit_report.passed:
        return _record_error(state, "publish_prepare", f"audit blocked: {audit_report.failed_checks}")

    text = state["brand_draft"]
    title = text.lstrip().splitlines()[0].lstrip("# ").strip()
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    intro = next((ln for ln in text.splitlines() if ln.strip() and not ln.startswith("#")), "")
    payload = PublishPayload(
        title=title,
        slug=slug,
        meta_description=intro[:155],
        content=text,
    )
    return {"publish_payload": payload.model_dump()}
