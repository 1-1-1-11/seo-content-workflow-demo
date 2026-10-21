# 安全策略

## 支持的版本

| 版本 | 状态 |
| --- | --- |
| 0.1.x | 接受报告 |

## 这个仓库是什么

本地 mock 演示。默认代码不会访问 LLM、搜索接口或 WordPress。`.env.example` 里的地址和口令都是占位符，程序不会读取那些被注释掉的变量。

`artifacts/` 可能含有你在本地输入的关键词。该目录已被忽略，请不要把它提交进仓库。

## 报告问题

请使用 GitHub 的 [Private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)，不要开公开 issue。

报告里不要包含可用的 API key、口令、客户名称、生产站点或未公开的提示词。用最小的复现说明问题即可。

维护者需要在仓库设置里打开 Private vulnerability reporting，这个入口才会出现。
