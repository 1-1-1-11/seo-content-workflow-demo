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

stages = [
    ("serp", "SERP"),
    ("outline", "大纲"),
    ("draft", "初稿"),
    ("brand", "品牌改写"),
    ("audit", "审核"),
    ("payload", "发布载荷"),
]
chips = "".join(
    f'<li class="done">{label}</li>' for _, label in stages
)
competitors = "".join(f"<li>{t}</li>" for t in serp["competitor_titles"][:5])
paa = "".join(f"<li>{q}</li>" for q in serp["paa_questions"][:4])
sections = "".join(
    f"<tr><td>{s['h2']}</td><td class='mute'>{s['intent']}</td></tr>"
    for s in outline["sections"]
)
checks = "".join(
    f"<tr><td>{c['name']}</td>"
    f"<td class='{'ok' if c['ok'] else 'bad'}'>{'通过' if c['ok'] else '拦住'}</td>"
    f"<td class='mute'>{c['detail']}</td></tr>"
    for c in audit["checks"]
)
excerpt = "\n".join(brand.splitlines()[:12])
audit_state = "审核通过" if audit.get("passed") else "审核未过"
audit_cls = "ok" if audit.get("passed") else "bad"

html = f"""<!doctype html>
<html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>seo pipeline · {run_dir.name}</title>
<style>
:root {{
  --bg:#f3f2ee; --panel:#fff; --line:#ddd9d0; --text:#1f2320;
  --muted:#6d736c; --ok:#2f6b45; --bad:#9b3b32; --accent:#2a4a3c;
  --mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  --sans: "IBM Plex Sans", "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
}}
*{{box-sizing:border-box;margin:0}}
body{{background:var(--bg);color:var(--text);font:13px/1.5 var(--sans);padding:0}}
.top{{display:flex;align-items:baseline;gap:10px;padding:12px 18px;border-bottom:1px solid var(--line);background:var(--panel)}}
.brand{{font-family:var(--mono);font-weight:600;font-size:13px}}
.meta{{color:var(--muted);font-family:var(--mono);font-size:11px;flex:1}}
.state{{font-family:var(--mono);font-size:11px;color:var(--ok)}}
.state.bad{{color:var(--bad)}}
.main{{padding:16px 18px 28px;max-width:980px}}
.steps{{list-style:none;display:flex;gap:0;border:1px solid var(--line);background:var(--panel);margin-bottom:14px;padding:0}}
.steps li{{flex:1;padding:8px 10px;font-size:12px;border-right:1px solid var(--line);color:var(--muted)}}
.steps li:last-child{{border-right:none}}
.steps li.done{{color:var(--text);font-weight:550}}
.layout{{display:grid;grid-template-columns:1.05fr .95fr;gap:12px}}
.box{{background:var(--panel);border:1px solid var(--line);padding:12px 13px}}
.box h2{{font-size:12px;font-weight:600;color:var(--accent);margin-bottom:8px}}
.box h3{{font-size:11px;color:var(--muted);font-weight:500;margin:10px 0 6px}}
ul{{padding-left:16px;margin:0;color:#333;font-size:12.5px}}
li{{margin:2px 0}}
table{{width:100%;border-collapse:collapse;font-size:12.5px}}
td{{padding:5px 4px;border-top:1px solid #ece8df;vertical-align:top}}
tr:first-child td{{border-top:none}}
.mute{{color:var(--muted)}}
.ok{{color:var(--ok);font-family:var(--mono);font-weight:600}}
.bad{{color:var(--bad);font-family:var(--mono);font-weight:600}}
pre{{background:#1b1f1c;color:#d5dbd4;border-radius:2px;padding:10px 11px;font:11.5px/1.55 var(--mono);white-space:pre-wrap;margin-top:6px}}
.kv{{font-family:var(--mono);font-size:12px;line-height:1.7}}
.kv b{{font-weight:500;color:var(--muted);display:inline-block;min-width:52px}}
.foot{{margin-top:14px;color:var(--muted);font-size:11px;font-family:var(--mono)}}
</style></head><body>
<div class="top">
  <div class="brand">seo pipeline</div>
  <div class="meta">{run_dir.name} · {serp["keyword"]} · mock</div>
  <div class="state {audit_cls}">{audit_state}</div>
</div>
<div class="main">
<ol class="steps">{chips}</ol>
<div class="layout">
  <div class="box">
    <h2>SERP</h2>
    <h3>竞品标题</h3>
    <ul>{competitors}</ul>
    <h3>People Also Ask</h3>
    <ul>{paa}</ul>
  </div>
  <div class="box">
    <h2>大纲</h2>
    <table>{sections}</table>
  </div>
  <div class="box">
    <h2>审核</h2>
    <table>{checks}</table>
  </div>
  <div class="box">
    <h2>发布载荷</h2>
    <div class="kv">
      <div><b>title</b> {payload["title"]}</div>
      <div><b>slug</b> {payload["slug"]}</div>
      <div><b>status</b> {payload["status"]}</div>
      <div><b>meta</b> {payload["meta_description"][:90]}...</div>
    </div>
    <h3>品牌改写稿节选</h3>
    <pre>{excerpt[:480]}</pre>
  </div>
</div>
<div class="foot">产物在 artifacts/ · 默认只出 preview · WordPress 草稿要人工确认后再建</div>
</div>
</body></html>"""

out = Path("assets") / "_run_report.html"
out.write_text(html, encoding="utf-8")
print(out.resolve())
