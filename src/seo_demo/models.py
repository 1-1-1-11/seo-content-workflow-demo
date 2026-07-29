"""阶段间传递的结构化模型:schema 变化在类型层暴露,而不是在运行时炸开。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SerpResult(BaseModel):
    keyword: str
    intent: str = Field(description="主导搜索意图:informational / commercial / transactional")
    competitor_titles: list[str]
    paa_questions: list[str] = Field(description="People Also Ask 问题")


class Section(BaseModel):
    h2: str
    intent: str = Field(description="本节覆盖的搜索意图")
    key_points: list[str]


class Outline(BaseModel):
    h1: str
    sections: list[Section]


class Check(BaseModel):
    name: str
    ok: bool
    detail: str = ""


class AuditReport(BaseModel):
    passed: bool
    checks: list[Check]

    @property
    def failed_checks(self) -> list[Check]:
        return [c for c in self.checks if not c.ok]


class BrandProfile(BaseModel):
    brand_voice: str
    positioning: str
    differentiators: list[str]
    forbidden_claims: list[str] = Field(default_factory=list)


class PublishPayload(BaseModel):
    """人工确认后交给 WordPress 的发布载荷。系统从不自动发布。"""

    title: str
    slug: str
    meta_description: str
    content: str
    status: str = "draft"
