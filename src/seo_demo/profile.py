"""读取品牌 profile。配置和代码分开，示例文件可以公开。"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from .models import BrandProfile


class ProfileError(Exception):
    """配置缺失或无法解析。CLI 把它转成退出码 2，而不是堆栈。"""


def discover_profile_path() -> Path | None:
    """从当前目录向上找示例 profile，并回退到源码树里的那一份。"""
    roots: list[Path] = [Path.cwd(), *Path.cwd().parents]
    package_root = Path(__file__).resolve().parents[2]
    if package_root not in roots:
        roots.append(package_root)
    seen: set[Path] = set()
    for root in roots:
        candidate = (root / "config" / "prompt_profile.example.yaml").resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.is_file():
            return candidate
    return None


def _as_str_list(value: object, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ProfileError(f"{field} 必须是字符串列表")
    return list(value)


def load_profile(path: Path) -> BrandProfile:
    if not path.is_file():
        raise ProfileError(f"找不到品牌配置文件: {path}")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ProfileError(f"品牌配置不是合法 YAML: {path}") from exc
    if not isinstance(raw, dict):
        raise ProfileError(f"品牌配置必须是 YAML 映射: {path}")
    kb = raw.get("company_kb") or {}
    if not isinstance(kb, dict):
        raise ProfileError("company_kb 必须是映射")
    try:
        return BrandProfile(
            brand_voice=str(raw.get("brand_voice") or "neutral"),
            positioning=str(kb.get("positioning") or ""),
            differentiators=_as_str_list(kb.get("differentiators"), "differentiators"),
            forbidden_claims=_as_str_list(kb.get("forbidden_claims"), "forbidden_claims"),
        )
    except ValidationError as exc:
        raise ProfileError(f"品牌配置字段无法解析: {path}") from exc
