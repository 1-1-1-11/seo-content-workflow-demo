# 贡献

这个仓库是离线演示。改动应该让 `pytest` 和 `ruff check` 继续通过，并且不要把真实数据带进来。

## 环境

需要 Python 3.11 或更高版本。

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

## 检查

```bash
ruff check .
pytest
python -m seo_demo.run --keyword "industrial gearbox motor"
```

CI 在 Python 3.11 上执行同样的 lint 和测试。

## 提交内容

- 不要提交 `.env`、`artifacts/` 或 `assets/_run_report.html`。
- 不要提交 API key、口令、客户名称、真实站点或本机绝对路径。示例一律用占位符，例如 `replace-me` 和 `https://cms.example.com`。
- 品牌语气放在 profile YAML 里，不要写进节点代码。
- 行为变化请补一个测试，并在 `CHANGELOG.md` 的 `Unreleased` 或对应版本下记一笔。

## Pull request

说明改了什么、怎么验证的。如果流水线的产物格式变了，请更新 README 里的示例输出。
