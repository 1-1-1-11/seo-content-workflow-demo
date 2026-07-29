# -*- coding: utf-8 -*-
"""从最新一次 artifacts 生成单页运行报告 HTML(用于 README 截图)。"""
import json
from pathlib import Path

run_dir = sorted(Path("artifacts").iterdir())[-1]
serp = json.loads((run_dir / "01_serp.json").read_text(encoding="utf-8"))
outline = json.loads((run_dir / "02_outline.json").read_text(encoding="utf-8"))
audit = json.loads((run_dir / "05_audit.json").read_text(encoding="utf-8"))
payload = json.loads((run_dir / "06_publish_payload.json").read_text(encoding="utf-8"))
brand = (run_dir / "04_brand_draft.md").read_text(encoding="utf-8")

stages = ["SERP 研究", "架构 Agent", "写作 Agent", "品牌改写", "审核 Agent", "发布载荷"]
chips = "".join(
    f'<div class="stage"><div class="dot"></div>{s}</div>' for s in stages)
competitors = "".join(f"<li>{t}</li>" for t in serp["competitor_titles"])
paa = "".join(f"<li>{q}</li>" for q in serp["paa_questions"])
sections = "".join(
    f'<tr><td>{s["h2"]}</td><td><span class="tag">{s["intent"]}</span></td></tr>'
    for s in outline["sections"])
checks = "".join(
    f'<tr><td>{c["name"]}</td><td class="{"ok" if c["ok"] else "bad"}">{"PASS" if c["ok"] else "BLOCK"}</td><td>{c["detail"]}</td></tr>'
    for c in audit["checks"])
excerpt = "\n".join(brand.splitlines()[:14])

html = f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><style>
* {{ box-sizing: border-box; margin: 0; }}
body {{ font-family: "Segoe UI", "Microsoft YaHei", sans-serif; background: #f6f7f4; color: #1c2321; padding: 34px 44px; }}
h1 {{ font-size: 21px; }}
.meta {{ color: #6b7280; font-size: 12px; margin: 4px 0 18px; font-family: Consolas, monospace; }}
.pipeline {{ display: flex; gap: 0; margin-bottom: 22px; }}
.stage {{ flex: 1; background: #fff; border: 1px solid #dfe3dd; border-left: none; padding: 9px 10px; font-size: 12px; font-weight: 600; display: flex; align-items: center; gap: 7px; }}
.stage:first-child {{ border-left: 1px solid #dfe3dd; border-radius: 6px 0 0 6px; }}
.stage:last-child {{ border-radius: 0 6px 6px 0; background: #0f4c5c; color: #fff; }}
.dot {{ width: 7px; height: 7px; border-radius: 50%; background: #2e8b57; flex: none; }}
.stage:last-child .dot {{ background: #ffd166; }}
.grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
.card {{ background: #fff; border: 1px solid #dfe3dd; border-radius: 8px; padding: 14px 16px; }}
.card h2 {{ font-size: 13px; color: #0f4c5c; margin-bottom: 8px; letter-spacing: .5px; }}
ul {{ padding-left: 17px; font-size: 12px; line-height: 1.75; color: #374151; }}
table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
td {{ border-top: 1px solid #eef1ec; padding: 5px 6px; }}
tr:first-child td {{ border-top: none; }}
.tag {{ background: #e8f0ee; color: #0f4c5c; border-radius: 4px; padding: 1px 7px; font-size: 11px; }}
.ok {{ color: #2e8b57; font-weight: 700; font-family: Consolas, monospace; }}
.bad {{ color: #c0392b; font-weight: 700; font-family: Consolas, monospace; }}
pre {{ background: #10161a; color: #c9d4d0; border-radius: 6px; padding: 12px 14px; font-size: 11px; line-height: 1.6; white-space: pre-wrap; font-family: Consolas, monospace; }}
.pass {{ display: inline-block; background: #2e8b57; color: #fff; font-size: 11px; font-weight: 700; border-radius: 4px; padding: 2px 10px; margin-left: 8px; }}
</style></head><body>
<h1>SEO Content Workflow · 运行报告 <span class="pass">AUDIT PASSED</span></h1>
<div class="meta">run_id: {run_dir.name} &nbsp;|&nbsp; keyword: "{serp["keyword"]}" &nbsp;|&nbsp; mode: mock(确定性,无外部 API)</div>
<div class="pipeline">{chips}</div>
<div class="grid">
  <div class="card"><h2>01 · SERP 研究 — 竞品标题</h2><ul>{competitors}</ul>
    <h2 style="margin-top:10px">People Also Ask</h2><ul>{paa}</ul></div>
  <div class="card"><h2>02 · 架构 Agent — 大纲与意图映射</h1></h2><table>{sections}</table></div>
  <div class="card"><h2>05 · 审核 Agent — 硬性检查</h2><table>{checks}</table></div>
  <div class="card"><h2>06 · 发布载荷(人工确认后才创建草稿)</h2>
    <pre>title: {payload["title"]}
slug:  {payload["slug"]}
meta:  {payload["meta_description"][:80]}...
status: {payload["status"]}</pre>
    <h2 style="margin-top:10px">04 · 品牌改写稿(节选)</h2>
    <pre>{excerpt[:520]}</pre></div>
</div>
</body></html>"""

out = Path("assets") / "_run_report.html"
out.write_text(html, encoding="utf-8")
print(out.resolve())
