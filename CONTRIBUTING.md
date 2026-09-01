# 贡献指南 / Contributing Guide

[English](#english) | [中文](#中文)

欢迎任何形式的贡献:Issue、PR、文档改进、demo 想法。

## 中文

### 提交 Issue

- 先搜索已有 Issue,避免重复;
- Bug 请附带:Python 版本、复现步骤、报错信息、`data.db` 是否清空重试过;
- 功能建议请说明:使用场景、期望行为。

### 提交 PR

1. Fork 本仓库,从 `master` 拉出功能分支;
2. 遵循现有代码风格:模块顶部 docstring、类型注解、与周围注释密度一致;
3. 新增工具请放在 `app/agent/tools/`,实现 `Tool` 接口并在 `app/agent/tools/__init__.py` 登记;
4. 提交前自测:启动服务后跑 `python _smoke_test.py`,确保 `ALL PASSED`;
5. PR 描述里写清:改了什么、为什么、如何验证。

### 约定

- 主 README 为中文,英文版同步维护 `README.en.md`;文档改动需两版一致;
- 不提交任何密钥;涉及 `.env` 只改 `.env.example`;
- 不提交 `data.db`、`__pycache__`、`.idea` 等本地产物。

---

## English

Any contribution is welcome: issues, PRs, doc improvements, demo ideas.

### Issues

- Search existing issues first;
- For bugs include: Python version, reproduction steps, error messages, whether a fresh `data.db` was tried;
- For features describe: the scenario and expected behavior.

### Pull Requests

1. Fork and branch from `master`;
2. Match the existing style: module docstrings, type annotations, comment density;
3. New tools go in `app/agent/tools/` — implement the `Tool` interface and register in `app/agent/tools/__init__.py`;
4. Self-test before submitting: start the server and run `python _smoke_test.py` until `ALL PASSED`;
5. Describe in the PR: what changed, why, and how it was verified.

### Conventions

- The main README is in Chinese; keep `README.en.md` in sync for doc changes;
- Never commit secrets; touch only `.env.example` for env-related changes;
- Never commit `data.db`, `__pycache__`, `.idea`, or other local artifacts.
