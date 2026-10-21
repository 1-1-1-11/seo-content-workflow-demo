"""纯文本小工具：slug、禁用词和导语。不依赖 LLM。"""

from __future__ import annotations

import hashlib
import re


def slugify(text: str, *, sep: str = "-", max_len: int = 80) -> str:
    """把标题收成 URL / 目录安全的片段。没有 ASCII 时用稳定短哈希，避免空 slug。"""
    slug = re.sub(r"[^a-z0-9]+", sep, text.lower()).strip(sep)
    if max_len > 0:
        slug = slug[:max_len].strip(sep)
    if slug:
        return slug
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]
    fallback = f"kw{sep}{digest}"
    if max_len > 0:
        return fallback[:max_len].strip(sep)
    return fallback


def find_forbidden_claims(text: str, claims: list[str]) -> list[str]:
    """按词边界匹配禁用表述。空规则忽略；`No.1` 不会误伤 `No.10`。"""
    hits: list[str] = []
    for claim in claims:
        needle = claim.strip()
        if not needle:
            continue
        pattern = re.compile(
            rf"(?<![A-Za-z0-9]){re.escape(needle)}(?![A-Za-z0-9])",
            re.IGNORECASE,
        )
        if pattern.search(text):
            hits.append(needle)
    return hits


def article_intro(text: str, limit: int = 155) -> str:
    """取正文第一段做 meta description，跳过标题、引用和列表。"""
    paragraph: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            if paragraph:
                break
            continue
        if stripped.startswith(("#", ">", "- ", "* ")):
            if paragraph:
                break
            continue
        paragraph.append(stripped)

    raw = " ".join(paragraph)
    raw = re.sub(r"\*\*(.+?)\*\*", r"\1", raw)
    raw = re.sub(r"`([^`]+)`", r"\1", raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    if len(raw) <= limit:
        return raw
    cut = raw[:limit].rsplit(" ", 1)[0].strip()
    if len(cut) >= limit // 2:
        return cut
    return raw[:limit].strip()
