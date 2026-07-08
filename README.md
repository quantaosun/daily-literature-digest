# Daily Literature Digest

每天自动检索最新化学文献，用 LLM 生成英文摘要，发到自己邮箱。

**追踪领域：** 有机反应机理、有机合成、全合成、药物化学、DEL 化合物库

**数据源：** arXiv + PubMed

**费用：** GitHub Actions 免费 + DeepSeek API 一天几分钱

## 配置方式（只需要 3 个 Secrets）

在 GitHub 仓库的 **Settings → Secrets and variables → Actions** 添加：

| Secret | 说明 |
|--------|------|
| `LLM_API_KEY` | DeepSeek API Key（去 [platform.deepseek.com](https://platform.deepseek.com) 注册） |
| `SMTP_USER` | 你的邮箱地址 |
| `SMTP_PASSWORD` | SMTP 授权码（见下方） |

可选（有默认值，不用配也行）：
| Secret | 默认值 |
|--------|--------|
| `SMTP_SERVER` | `smtp.qq.com` |
| `SMTP_PORT` | `465` |
| `LLM_BASE_URL` | `https://api.deepseek.com` |
| `LLM_MODEL` | `deepseek-chat` |

## QQ邮箱 获取 SMTP 授权码

1. 登录 QQ邮箱 → 设置 → 账户
2. 开启 **POP3/SMTP 服务**
3. 生成的 **授权码** 填入 `SMTP_PASSWORD`

其他邮箱（163、Gmail 等）同理，改 `SMTP_SERVER` 和 `SMTP_PORT` 即可。

## 启动

配置好 Secrets 后，每天 **北京时间 9:00** 自动运行。也可以去 **Actions → Daily Literature Digest → Run workflow** 手动触发测试。

邮件会自动发到你的 `SMTP_USER` 邮箱。
