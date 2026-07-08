# Daily Literature Digest

Automatically search PubMed for latest chemistry papers, summarize them with LLM, and email yourself a daily digest.

**Tracked topics:** organic synthesis, total synthesis, reaction mechanism, catalysis, medicinal chemistry, DNA-encoded library (DEL), C-H activation, cross-coupling, enantioselective, organocatalysis, photocatalysis, drug discovery

**Data source:** PubMed (NCBI E-utilities, free, no API key required)

**Cost:** GitHub Actions (free) + DeepSeek API (~¥0.01/day)

---

## Quick Start

### 1. Fork this repo

Click the Fork button on GitHub.

### 2. Add 3 Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Description |
|--------|-------------|
| `LLM_API_KEY` | DeepSeek API Key from [platform.deepseek.com](https://platform.deepseek.com) |
| `MAIL` | Your email address (sender & recipient) |
| `MAIL_PW` | SMTP password / app-specific password |

Optional (have defaults, skip if not needed):
| Secret | Default |
|--------|---------|
| `MAIL_SERVER` | `smtp.qq.com` |
| `MAIL_PORT` | `465` |
| `LLM_BASE_URL` | `https://api.deepseek.com` |
| `LLM_MODEL` | `deepseek-chat` |

### 3. Run

The workflow runs daily at **9:00 AM Beijing Time (1:00 UTC)**. You can also manually trigger it:

**Actions → Daily Literature Digest → Run workflow**

---

## Customize Keywords

Edit `KEYWORDS` in `digest.py` (around line 47):

```python
KEYWORDS = [
    "organic synthesis",
    "total synthesis",
    "reaction mechanism",
    # add or remove keywords here
]
```

---

## How It Works

```
PubMed API (free, no key)
       ↓
  Fetch papers matching keywords from last 60 days
       ↓
  Summarize each paper with DeepSeek LLM (English)
       ↓
  Send email digest to yourself via SMTP
```

**Tech stack:** Python 3.11 + `requests` | GitHub Actions | PubMed E-utilities | DeepSeek API

## Email SMTP Setup

### QQ Mail
1. Login to [mail.qq.com](https://mail.qq.com) → Settings → Account
2. Enable **POP3/SMTP service**
3. Use the generated authorization code as `MAIL_PW`

### Other Providers
| Provider | SMTP Server | Port |
|----------|-------------|------|
| QQ Mail | `smtp.qq.com` | 465 |
| 163 Mail | `smtp.163.com` | 465 |
| Gmail | `smtp.gmail.com` | 587 |
| Outlook | `smtp-mail.outlook.com` | 587 |

---

## License

MIT
