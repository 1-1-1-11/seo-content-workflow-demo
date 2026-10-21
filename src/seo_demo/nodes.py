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
from .textutil import article_intro, find_forbidden_claims, slugify

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
    body = text.lstrip()
    hits = find_forbidden_claims(text, profile.forbidden_claims)
    h1_count = len(re.findall(r"(?m)^# ", body))
    h2_count = len(re.findall(r"(?m)^## ", text))

    checks = [
        Check(
            name="forbidden_claims",
            ok=not hits,
            detail=", ".join(hits) if hits else "clean",
        ),
        Check(
            name="has_h1",
            ok=h1_count == 1 and body.startswith("# "),
            detail=f"found {h1_count} H1, need exactly 1",
        ),
        Check(
            name="min_sections",
            ok=h2_count >= 4,
            detail=f"found {h2_count} H2 sections, need >= 4",
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
        failed = ", ".join(check.name for check in audit_report.failed_checks) or "unknown"
        return _record_error(state, "publish_prepare", f"audit blocked: {failed}")

    text = state["brand_draft"]
    title = text.lstrip().splitlines()[0].lstrip("# ").strip()
    payload = PublishPayload(
        title=title,
        slug=slugify(title, sep="-", max_len=80),
        meta_description=article_intro(text),
        content=text,
        status="draft",
    )
    return {"publish_payload": payload.model_dump()}
