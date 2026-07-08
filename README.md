# Daily Literature Digest

> 📬 **每天自动检索 PubMed 最新文献 → DeepSeek 摘要 → 邮件推送到你邮箱**

[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-自动运行-blue)](https://github.com/quantaosun/daily-literature-digest/actions)
[![Python](https://img.shields.io/badge/Python-3.11-green)](https://www.python.org/)
[![DeepSeek](https://img.shields.io/badge/LLM-DeepSeek%20Chat-red)](https://platform.deepseek.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## ⚡ 如何使用

### 1. Fork 本仓库
点击右上角 **Fork** 按钮。

### 2. 配置 3 个 Secrets
仓库 → **Settings → Secrets and variables → Actions → New repository secret**

| Secret | 说明 |
|--------|------|
| `LLM_API_KEY` | DeepSeek API Key（[platform.deepseek.com](https://platform.deepseek.com) 注册） |
| `MAIL` | 你的邮箱（如 `yourname@qq.com`） |
| `MAIL_PW` | SMTP 授权码（见下方 QQ Mail 设置） |

### 3. ✅ 完成，自动运行

配置好后，每天 **北京时间 9:00（UTC 1:00）** 自动运行。你也可以手动触发：

**Actions → Daily Literature Digest → Run workflow**

> **5 分钟后检查邮箱**，你会收到当天的文献摘要邮件。

---

## ⏰ 默认执行频率

- **北京时间：** 每天 **09:00**
- **UTC 时间：** 每天 **01:00**
- 可在 `.github/workflows/daily-digest.yml` 中修改 `cron` 表达式调整频率

---

## 📋 本仓库由 Claude Code 协助编写

本项目由 [Claude Code](https://claude.ai/code)（Anthropic 的 AI 编程助手）参与开发和代码审查。

如需二次开发或修改功能：

1. **阅读 [`CLAUDE.md`](CLAUDE.md)** — 记录了完整的项目架构、代码流程、配置说明和开发约定
2. 将这个仓库 clone 到本地后，用 Claude Code 打开，它会自动读取 `CLAUDE.md` 理解项目
3. 然后直接对 Claude 提需求即可（如"增加新的文献源"、"改为 Slack 推送"等）

---

## Customize Keywords

<details>
<summary>🧪 Chemistry (default)</summary>

```python
KEYWORDS = [
    "organic synthesis",
    "total synthesis",
    "reaction mechanism",
    "catalysis",
    "medicinal chemistry",
    "DNA-encoded library",
    "C-H activation",
    "cross-coupling",
    "enantioselective",
    "organocatalysis",
    "photocatalysis",
    "drug discovery",
]
```
</details>

<details>
<summary>🧬 Biology & Biomedical</summary>

```python
KEYWORDS = [
    "CRISPR",
    "gene editing",
    "protein structure",
    "single cell",
    "immunotherapy",
    "cell signaling",
    "proteomics",
    "genomics",
    "RNA biology",
]
```
</details>

<details>
<summary>🤖 Machine Learning & AI</summary>

```python
KEYWORDS = [
    "large language model",
    "deep learning",
    "reinforcement learning",
    "computer vision",
    "natural language processing",
    "neural network",
    "transformer",
    "diffusion model",
    "representation learning",
]
```
</details>

<details>
<summary>🔬 Physics & Materials</summary>

```python
KEYWORDS = [
    "quantum computing",
    "topological insulator",
    "2D materials",
    "superconductivity",
    "photovoltaic",
    "battery",
    "catalyst",
    "nanomaterials",
    "metamaterial",
]
```
</details>

**修改方式：** 编辑 `digest.py` 中的 `KEYWORDS` 列表 → commit → push，下次自动运行生效。

---

## Email Setup

### QQ Mail（推荐）

<details>
<summary>📱 展开查看详细步骤</summary>

1. 登录 [mail.qq.com](https://mail.qq.com)
2. 设置 → 账户
3. 开启 **POP3/SMTP 服务**
4. 按短信验证后获取 **16 位授权码**
5. 填入 GitHub Secrets 的 `MAIL_PW`

</details>

### Other Providers

| Provider | SMTP Server | Port |
|----------|-------------|------|
| QQ Mail | `smtp.qq.com` | 465 |
| 163 Mail | `smtp.163.com` | 465 |
| Gmail | `smtp.gmail.com` | 587 |
| Outlook | `smtp-mail.outlook.com` | 587 |

非 QQ 邮箱需额外设置 `MAIL_SERVER` 和 `MAIL_PORT` Secrets。

---

## Architecture

```
PubMed API (free, no key)
       ↓
Search papers from last 60 days matching your keywords
       ↓
Summarize each paper with DeepSeek LLM (English)
       ↓
Send email digest to yourself via SMTP
```

**Tech stack:** Python 3.11 + `requests` | GitHub Actions | PubMed E-utilities | DeepSeek API

---

## License

MIT
