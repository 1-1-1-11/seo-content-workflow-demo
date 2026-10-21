# Changelog

本文件遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 的格式，版本号遵循语义化版本。

## [0.1.0] - 2026-10-21

公开的离线演示。不包含客户数据、真实提示词或密钥。

### Added

- 六步内容流水线：SERP、大纲、初稿、品牌改写、审核、发布载荷。发布载荷始终是 `draft`。
- 用环境变量或 `.env` 配置关键词、模式、品牌 profile 和产物目录。
- 示例品牌配置、Ruff、pytest，以及跑 lint 和测试的 GitHub Actions。
- 贡献指南、安全策略、Issue / PR 模板。

### Fixed

- 发布摘要改为正文导语，不再把品牌引用块和 markdown 标记写进 `meta_description`。
- 审核要求恰好一个 H1。禁用词按词边界匹配，不再误伤 `unguaranteed`、`No.10`，空规则也不会把稿件全部拦住。
- 审核未通过或上游解析失败时，已经完成的阶段仍会落盘。
- 非 ASCII 关键词不再生成空的 run 目录名或空 slug。同一秒内重复运行不会覆盖上一次产物。
- 缺失、空文件或格式不对的 profile，以及空的产物目录，会返回明确的退出码，而不是堆栈。
