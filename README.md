# seo-content-workflow-demo

关键词进去，一篇能检查的 SEO 草稿出来。这是生产流水线的脱敏版：结构差不多，客户数据、真实提示词和密钥都不在这里。本地 mock 就能跑完。

## 怎么跑

```bash
git clone https://github.com/1-1-1-11/seo-content-workflow-demo.git
cd seo-content-workflow-demo
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m seo_demo.run --keyword "industrial gearbox motor" --mode mock
```

跑完看 `artifacts/<run_id>/`：

```text
01_serp.json        SERP：竞品标题、PAA、意图
02_outline.json     大纲
03_draft.md         初稿
04_brand_draft.md   按品牌配置改写后的稿
05_audit.json       审核结果
06_publish_payload.json
```

想把最近一次跑数渲成单页报告：

```bash
python gen_report.py
# 打开 assets/_run_report.html
```

![一次 mock 跑完的报告](assets/pipeline-run.png)

## 流水线在干什么

六步：SERP → 大纲 → 初稿 → 品牌改写 → 审核 → 发布载荷。每步产物落盘，想卡在哪步看就看哪步。

品牌改写靠两份和代码分开的配置（见 `config/prompt_profile.example.yaml`）：语气、公司怎么讲自己、以及一串**不准写**的词。审核阶段会硬拦 `forbidden_claims`，不是提醒，是过不了。

默认只出本地 preview。WordPress 草稿要人确认后再建，系统自己不会发。

## 和正式版差在哪

正式版节点更多，还有操作台和多客户后台；这里收成六步 + CLI，方便公开看。数据全是假的。

```text
src/seo_demo/
  state.py / models.py / nodes.py / graph.py / run.py / mock_llm.py
config/prompt_profile.example.yaml
tests/test_pipeline.py
```
