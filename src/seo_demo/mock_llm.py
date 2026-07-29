"""确定性假 LLM:mock 模式与测试使用。

生产环境中这里是一个 OpenAI 兼容客户端(按阶段路由到不同模型);
Demo 中用模板生成确定性输出,保证 CI 不依赖任何外部服务。
"""

from __future__ import annotations

import json


class MockLLM:
    """按任务类型返回确定性结果。输出格式与真实 LLM 约定一致(JSON / markdown)。"""

    def complete(self, task: str, payload: dict) -> str:
        handler = getattr(self, f"_{task}", None)
        if handler is None:
            raise ValueError(f"unknown task: {task}")
        return handler(payload)

    # ------------------------------------------------------------------ SERP
    def _serp(self, payload: dict) -> str:
        kw = payload["keyword"]
        return json.dumps(
            {
                "keyword": kw,
                "intent": "commercial",
                "competitor_titles": [
                    f"Top 10 {kw} Manufacturers and Suppliers",
                    f"How to Choose a {kw}: Buyer's Guide",
                    f"{kw} Price, Specifications & Applications",
                ],
                "paa_questions": [
                    f"What is a {kw} used for?",
                    f"How much does a {kw} cost?",
                    f"What are the types of {kw}?",
                ],
            },
            ensure_ascii=False,
        )

    # -------------------------------------------------------------- 大纲
    def _outline(self, payload: dict) -> str:
        kw = payload["keyword"]
        return json.dumps(
            {
                "h1": f"{kw.title()}: Specifications, Selection & Buying Guide",
                "sections": [
                    {
                        "h2": f"What Is a {kw.title()}?",
                        "intent": "informational",
                        "key_points": ["definition", "working principle", "core components"],
                    },
                    {
                        "h2": "Key Specifications to Compare",
                        "intent": "commercial",
                        "key_points": ["power range", "efficiency class", "mounting type"],
                    },
                    {
                        "h2": "Common Applications",
                        "intent": "informational",
                        "key_points": ["conveyors", "pumps", "fans"],
                    },
                    {
                        "h2": "How to Choose the Right Model",
                        "intent": "transactional",
                        "key_points": ["load calculation", "duty cycle", "environment"],
                    },
                    {
                        "h2": "FAQ",
                        "intent": "informational",
                        "key_points": payload.get("paa_questions", []),
                    },
                ],
            },
            ensure_ascii=False,
        )

    # -------------------------------------------------------------- 初稿
    def _draft(self, payload: dict) -> str:
        outline = payload["outline"]
        lines = [f"# {outline['h1']}", ""]
        lines.append(
            f"Selecting the right equipment starts with understanding your load profile. "
            f"This guide walks through specifications, applications, and selection criteria."
        )
        lines.append("")
        for sec in outline["sections"]:
            lines.append(f"## {sec['h2']}")
            lines.append("")
            for point in sec["key_points"]:
                lines.append(f"- **{point}**: what buyers should verify before requesting a quote.")
            lines.append("")
        return "\n".join(lines)

    # ---------------------------------------------------------- 品牌改写
    def _brand(self, payload: dict) -> str:
        profile = payload["profile"]
        draft = payload["draft"]
        diffs = "\n".join(f"- {d}" for d in profile["differentiators"])
        brand_block = (
            f"\n\n> **Why buyers work with us**: {profile['positioning']}.\n"
            f"> Voice: {profile['brand_voice']}.\n\n"
            f"{diffs}\n"
        )
        # 品牌段插入 H1 之后,其余内容保持不变
        head, _, rest = draft.partition("\n")
        return head + brand_block + "\n" + rest


class BrokenLLM:
    """模拟上游异常:返回无法解析的内容,用于验证失败边界。"""

    def complete(self, task: str, payload: dict) -> str:
        return "<not-json>upstream returned garbage</not-json>"
