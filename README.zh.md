# Daily Literature Digest

> 📬 **自动搜索 PubMed → AI 摘要 → 邮件推送到你邮箱**

## 什么是 GitHub Actions？

**GitHub Actions** 是 GitHub 内置的免费自动化服务。你可以把它想象成一个云端机器人——它可以按时执行任务，也可以在你点按钮时运行。本项目就是用它在每天北京时间 9:00 自动运行文献摘要脚本，你完全不需要在自己电脑上跑任何东西。

> 无需服务器、无需配置定时任务、无需手动操作。只需 Fork 并添加密钥，剩下的交给 GitHub Actions。

## 工作原理

```
PubMed API（免费，无需密钥）
       ↓
搜索近 60 天内匹配关键词的论文
       ↓
用 DeepSeek 大模型生成摘要
       ↓
通过 SMTP 邮件发送到你的邮箱
```

GitHub Actions 每天 **北京时间 9:00** 自动执行。你也可以在 Actions 标签页手动触发。

---

## 设置（3 分钟）

**1. Fork 本仓库**（右上角）

**2. 添加 3 个 Secrets** → Settings → Secrets and variables → Actions → New repository secret：

| Secret | 填写内容 |
|--------|---------|
| `LLM_API_KEY` | 你的 DeepSeek API 密钥（[platform.deepseek.com](https://platform.deepseek.com)） |
| `MAIL` | 你的邮箱地址（如 `yourname@qq.com`） |
| `MAIL_PW` | SMTP 授权码 |

**3. 完成。** 下次定时运行会自动发送摘要。你也可以去 **Actions → Daily Literature Digest → Run workflow** 立即测试。

---

## 邮箱设置

| 邮箱提供商 | SMTP 服务器 | 端口 | 说明 |
|-----------|------------|------|------|
| QQ 邮箱 | `smtp.qq.com` | 465 | [开启 POP3/SMTP → 获取 16 位授权码](https://service.mail.qq.com/detail/0/75) |
| 163 邮箱 | `smtp.163.com` | 465 | 类似 QQ 邮箱 |
| Gmail | `smtp.gmail.com` | 587 | 使用[应用专用密码](https://support.google.com/accounts/answer/185833) |
| Outlook | `smtp-mail.outlook.com` | 587 | 使用应用专用密码 |

非 QQ 邮箱需要额外添加 `MAIL_SERVER` 和 `MAIL_PORT` Secrets。

---

## 自定义关键词

编辑 [`digest.py`](digest.py) 中的 `KEYWORDS` 列表（约第 45 行）。默认是化学方向：

```python
KEYWORDS = [
    "organic synthesis", "total synthesis", "reaction mechanism",
    "catalysis", "medicinal chemistry", "DNA-encoded library",
    "C-H activation", "cross-coupling", "drug discovery",
]
```

换成生物、机器学习、物理方向的关键词即可。每个关键词在 PubMed 的 `[Title/Abstract]` 中搜索，用 `OR` 组合。

---

## 局限性

- **仅限 PubMed** — 本工具只搜索 PubMed，并非所有期刊都被收录。
- **开放摘要** — 付费墙后的论文可能没有摘要或摘要不完整，不会获取全文。
- **免费 API 限制** — PubMed 的免费 API 有速率限制，脚本已尽量遵守，但高峰时段可能遗漏。

## 技术栈

- **Python 3.11** + `requests`
- **PubMed E-utilities**（免费，无需 API 密钥）
- **DeepSeek Chat**（或任何兼容 OpenAI 的模型）
- **GitHub Actions**（定时 + 手动触发）

---

## 许可

MIT
