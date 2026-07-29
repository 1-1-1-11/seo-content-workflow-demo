"""贯穿流水线的显式状态。阶段即节点,产物即状态。"""

from __future__ import annotations

from typing import Any, TypedDict


class WorkflowState(TypedDict, total=False):
    keyword: str
    run_mode: str  # mock | preview | publish
    profile: dict[str, Any]  # BrandProfile.model_dump()

    serp: dict[str, Any]          # SerpResult.model_dump()
    outline: dict[str, Any]       # Outline.model_dump()
    draft: str                    # 初稿 markdown
    brand_draft: str              # 品牌改写稿 markdown
    audit: dict[str, Any]         # AuditReport.model_dump()
    publish_payload: dict[str, Any]

    # 失败边界:阶段失败时记录原始输出,后续阶段跳过,不静默降级
    errors: list[dict[str, str]]  # {"stage": ..., "raw": ...}
