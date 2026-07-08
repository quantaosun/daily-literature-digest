# Daily Literature Digest

每天自动检索最新化学文献，用 LLM 生成英文摘要，发到邮箱。

**追踪领域：** 有机反应机理、有机合成、全合成、药物化学、DEL 化合物库

**数据源：** arXiv + PubMed

## 配置方式

在 GitHub 仓库的 **Settings → Secrets and variables → Actions** 中添加以下 Secrets：

| Secret | 说明 | 示例 |
|--------|------|------|
| `LLM_API_KEY` | DeepSeek API Key（必填） | `sk-xxxxxxxx` |
| `EMAIL_TO` | 收件邮箱 | `you@example.com` |
| `EMAIL_FROM` | 发件邮箱（同 SMTP_USER） | `you@qq.com` |
| `SMTP_USER` | SMTP 用户名（邮箱地址） | `you@qq.com` |
| `SMTP_PASSWORD` | SMTP 密码/授权码 | （见下方） |
| `SMTP_SERVER` | SMTP 服务器 | `smtp.qq.com`（默认） |
| `SMTP_PORT` | SMTP 端口 | `465`（默认） |

可选（有默认值，不填也行）：
| Secret | 默认值 |
|--------|--------|
| `LLM_BASE_URL` | `https://api.deepseek.com` |
| `LLM_MODEL` | `deepseek-chat` |

## QQ邮箱 SMTP 获取方式

1. 登录 QQ邮箱 → 设置 → 账户
2. 开启 **POP3/SMTP 服务**
3. 生成的 **授权码** 就是 `SMTP_PASSWORD`
4. `SMTP_USER` = 你的 QQ邮箱地址

## 启动方式

配置好 Secrets 后，这个 Action 会自动每天北京时间 9:00 运行。

也可以去 GitHub 仓库的 **Actions → Daily Literature Digest → Run workflow** 手动触发。
