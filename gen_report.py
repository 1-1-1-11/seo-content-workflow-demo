# -*- coding: utf-8 -*-
"""从最新一次 artifacts 生成单页运行报告 HTML（用于 README 截图）。"""
import html as html_lib
import json
import re
from pathlib import Path

run_dir = sorted(Path("artifacts").iterdir())[-1]
serp = json.loads((run_dir / "01_serp.json").read_text(encoding="utf-8"))
outline = json.loads((run_dir / "02_outline.json").read_text(encoding="utf-8"))
audit = json.loads((run_dir / "05_audit.json").read_text(encoding="utf-8"))
payload = json.loads((run_dir / "06_publish_payload.json").read_text(encoding="utf-8"))
brand = (run_dir / "04_brand_draft.md").read_text(encoding="utf-8")

CHECK_LABELS = {
    "forbidden_claims": "禁用表述",
    "has_h1": "标题结构",
    "min_sections": "章节数量",
    "min_length": "篇幅长度",
}
INTENT_LABELS = {
    "informational": "信息",
    "commercial": "商业",
    "transactional": "转化",
}
STAGES = [
    ("检索", True),
    ("大纲", True),
    ("初稿", True),
    ("品牌改写", True),
    ("审核", True),
    ("待发布", True),
]


def esc(s: str) -> str:
    return html_lib.escape(s, quote=True)


def md_to_simple_html(md: str) -> str:
    """极简 markdown → HTML，够演示预览用。"""
    lines = md.splitlines()
    out: list[str] = []
    in_ul = False
    in_bq = False

    def close_ul():
        nonlocal in_ul
        if in_ul:
            out.append("</ul>")
            in_ul = False

    def close_bq():
        nonlocal in_bq
        if in_bq:
            out.append("</blockquote>")
            in_bq = False

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            close_ul()
            close_bq()
            continue
        if line.startswith("> "):
            close_ul()
            if not in_bq:
                out.append('<blockquote class="note">')
                in_bq = True
            text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", esc(line[2:]))
            out.append(f"<p>{text}</p>")
            continue
        close_bq()
        if line.startswith("# "):
            close_ul()
            out.append(f"<h1>{esc(line[2:])}</h1>")
        elif line.startswith("## "):
            close_ul()
            out.append(f"<h2>{esc(line[3:])}</h2>")
        elif line.startswith("- "):
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", esc(line[2:]))
            out.append(f"<li>{text}</li>")
        else:
            close_ul()
            text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", esc(line))
            out.append(f"<p>{text}</p>")
    close_ul()
    close_bq()
    return "\n".join(out)


steps_html = "".join(
    f'<li class="done"><span class="n">{i}</span>{label}</li>'
    for i, (label, _) in enumerate(STAGES, 1)
)
competitors = "".join(f"<li>{esc(t)}</li>" for t in serp["competitor_titles"][:5])
paa = "".join(f"<li>{esc(q)}</li>" for q in serp["paa_questions"][:4])
sections = "".join(
    "<tr>"
    f"<td>{esc(s['h2'])}</td>"
    f"<td class='mute'>{esc(INTENT_LABELS.get(s['intent'], s['intent']))}</td>"
    "</tr>"
    for s in outline["sections"]
)
checks = "".join(
    "<tr>"
    f"<td>{esc(CHECK_LABELS.get(c['name'], c['name']))}</td>"
    f"<td class='{'ok' if c['ok'] else 'bad'}'>{'通过' if c['ok'] else '未通过'}</td>"
    f"<td class='mute'>{esc(c['detail'])}</td>"
    "</tr>"
    for c in audit["checks"]
)
draft_html = md_to_simple_html(brand)
audit_state = "审核通过" if audit.get("passed") else "审核未过"
audit_cls = "ok" if audit.get("passed") else "bad"
status_cn = {"draft": "草稿", "publish": "已发布"}.get(payload["status"], payload["status"])
meta = payload.get("meta_description") or ""
meta_short = meta.replace("\n", " ")[:80]
if len(meta) > 80:
    meta_short += "…"

page = f"""<!doctype html>
<html lang="zh"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>内容流水线 · {esc(serp['keyword'])}</title>
<style>
:root {{
  --bg:#f5f5f4;
  --panel:#ffffff;
  --line:#e7e5e4;
  --line-strong:#d6d3d1;
  --text:#1c1917;
  --muted:#78716c;
  --ok:#15803d;
  --ok-bg:#f0fdf4;
  --bad:#b91c1c;
  --bad-bg:#fef2f2;
  --accent:#0f766e;
  --soft:#fafaf9;
  --sans: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei",
           "Noto Sans CJK SC", "Segoe UI", system-ui, sans-serif;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--text);font:14px/1.55 var(--sans)}}
.top{{
  display:flex;align-items:center;gap:12px;
  padding:12px 20px;background:var(--panel);
  border-bottom:1px solid var(--line);
}}
.brand{{font-weight:600;font-size:14px;color:var(--text)}}
.meta{{color:var(--muted);font-size:13px;flex:1}}
.badge{{
  font-size:12px;padding:3px 10px;border-radius:999px;
  border:1px solid var(--line);color:var(--muted);background:var(--soft);
}}
.badge.ok{{color:var(--ok);border-color:#bbf7d0;background:var(--ok-bg)}}
.badge.bad{{color:var(--bad);border-color:#fecaca;background:var(--bad-bg)}}
.wrap{{max-width:1080px;margin:0 auto;padding:18px 20px 32px}}
.steps{{
  list-style:none;display:flex;gap:0;margin-bottom:16px;
  background:var(--panel);border:1px solid var(--line);border-radius:8px;
  overflow:hidden;
}}
.steps li{{
  flex:1;display:flex;align-items:center;gap:8px;
  padding:10px 12px;font-size:13px;color:var(--muted);
  border-right:1px solid var(--line);
}}
.steps li:last-child{{border-right:none}}
.steps li.done{{color:var(--text)}}
.steps .n{{
  width:20px;height:20px;border-radius:50%;
  display:inline-flex;align-items:center;justify-content:center;
  font-size:11px;font-weight:600;background:var(--soft);
  border:1px solid var(--line);color:var(--muted);flex-shrink:0;
}}
.steps li.done .n{{
  background:var(--ok-bg);border-color:#bbf7d0;color:var(--ok);
}}
.grid{{display:grid;grid-template-columns:1.45fr .9fr;gap:14px;margin-bottom:14px}}
.panel{{
  background:var(--panel);border:1px solid var(--line);
  border-radius:8px;padding:14px 16px;
}}
.panel h2{{
  font-size:13px;font-weight:600;margin-bottom:10px;
  display:flex;align-items:center;justify-content:space-between;
}}
.panel h2 .hint{{font-weight:400;color:var(--muted);font-size:12px}}
.panel h3{{
  font-size:12px;color:var(--muted);font-weight:500;
  margin:12px 0 6px;
}}
.draft{{
  background:var(--soft);border:1px solid var(--line);
  border-radius:6px;padding:16px 18px;max-height:420px;overflow:auto;
}}
.draft h1{{font-size:18px;line-height:1.35;margin-bottom:10px;font-weight:650}}
.draft h2{{font-size:14px;margin:14px 0 6px;font-weight:600;color:var(--text)}}
.draft p{{margin:6px 0;color:#292524;font-size:13.5px}}
.draft ul{{margin:6px 0 6px 18px;font-size:13.5px;color:#292524}}
.draft li{{margin:3px 0}}
.draft .note{{
  margin:8px 0 12px;padding:8px 12px;
  background:#fff;border-left:3px solid var(--accent);
  border-radius:0 4px 4px 0;font-size:13px;color:#44403c;
}}
.draft .note p{{margin:2px 0}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
td{{padding:7px 4px;border-top:1px solid var(--line);vertical-align:top}}
tr:first-child td{{border-top:none}}
.mute{{color:var(--muted)}}
.ok{{color:var(--ok);font-weight:600}}
.bad{{color:var(--bad);font-weight:600}}
.kv{{font-size:13px;line-height:1.75}}
.kv .row{{display:grid;grid-template-columns:56px 1fr;gap:8px}}
.kv .k{{color:var(--muted)}}
.kv .v{{word-break:break-all}}
.refs{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
ul.plain{{margin:0;padding-left:16px;font-size:13px;color:#292524}}
ul.plain li{{margin:3px 0}}
.foot{{margin-top:14px;color:var(--muted);font-size:12px}}
@media (max-width:860px){{
  .grid,.refs{{grid-template-columns:1fr}}
  .steps{{flex-wrap:wrap}}
  .steps li{{flex:1 1 40%;border-bottom:1px solid var(--line)}}
}}
</style>
</head><body>
<div class="top">
  <div class="brand">内容流水线</div>
  <div class="meta">{esc(serp['keyword'])} · 本地演示</div>
  <div class="badge {audit_cls}">{audit_state}</div>
</div>
<div class="wrap">
  <ol class="steps">{steps_html}</ol>
  <div class="grid">
    <div class="panel">
      <h2>品牌改写稿 <span class="hint">本步产物，便于对照审核项</span></h2>
      <div class="draft">{draft_html}</div>
    </div>
    <div>
      <div class="panel" style="margin-bottom:14px">
        <h2>审核结果</h2>
        <table>{checks}</table>
      </div>
      <div class="panel">
        <h2>发布信息 <span class="hint">status = draft</span></h2>
        <div class="kv">
          <div class="row"><span class="k">标题</span><span class="v">{esc(payload['title'])}</span></div>
          <div class="row"><span class="k">路径</span><span class="v">{esc(payload['slug'])}</span></div>
          <div class="row"><span class="k">状态</span><span class="v">{esc(status_cn)}</span></div>
          <div class="row"><span class="k">摘要</span><span class="v mute">{esc(meta_short)}</span></div>
        </div>
        <p class="mute" style="margin-top:10px;font-size:12px">当前为草稿。确认文案后再建 WordPress 草稿。</p>
      </div>
    </div>
  </div>
  <div class="refs">
    <div class="panel">
      <h2>检索参考</h2>
      <h3>竞品标题</h3>
      <ul class="plain">{competitors}</ul>
      <h3>大家还在问</h3>
      <ul class="plain">{paa}</ul>
    </div>
    <div class="panel">
      <h2>大纲</h2>
      <table>{sections}</table>
    </div>
  </div>
  <div class="foot">产物目录 artifacts/{esc(run_dir.name)} · 本地 mock 跑次</div>
</div>
</body></html>
"""

out = Path("assets") / "_run_report.html"
out.write_text(page, encoding="utf-8")
print(out.resolve())
