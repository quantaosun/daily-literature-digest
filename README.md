# Daily Literature Digest

> 📬 **Automatically search PubMed → summarize with AI → email the digest to you.**
>
> [🇨🇳 中文版](README.zh.md)

## What is GitHub Actions?

**GitHub Actions** is a free automation service built into GitHub. Think of it as a robot that can run tasks for you in the cloud — on a schedule, or whenever you press a button. This repo uses it to run the literature digest script every day at 9 AM Beijing time, so you don't need to run anything on your own computer.

> No servers to set up, no cron jobs to configure, no manual work. Just fork and add secrets — GitHub Actions handles the rest.

## How it works

```
PubMed API (free, no key needed)
       ↓
Search papers from last 60 days matching your keywords
       ↓
Summarize each paper with DeepSeek LLM
       ↓
Email the digest to you via SMTP
```

GitHub Actions runs this pipeline every day at **9:00 AM Beijing time** automatically. You can also trigger it manually from the Actions tab.

---

## Setup (3 minutes)

**1. Fork this repo** (top-right corner)

**2. Add 3 Secrets** to your fork → Settings → Secrets and variables → Actions → New repository secret:

| Secret | What to put |
|--------|------------|
| `LLM_API_KEY` | Your DeepSeek API key ([platform.deepseek.com](https://platform.deepseek.com)) |
| `MAIL` | Your email address (e.g. `yourname@qq.com`) |
| `MAIL_PW` | Your SMTP password / authorization code |

**3. Done.** The next scheduled run will send you a digest. Or go to **Actions → Daily Literature Digest → Run workflow** to test it immediately.

---

## Email setup

| Provider | SMTP Server | Port | Notes |
|----------|-------------|------|-------|
| QQ Mail | `smtp.qq.com` | 465 | [Enable POP3/SMTP → get 16-char auth code](https://service.mail.qq.com/detail/0/75) |
| 163 Mail | `smtp.163.com` | 465 | Similar to QQ |
| Gmail | `smtp.gmail.com` | 587 | Use an [App Password](https://support.google.com/accounts/answer/185833) |
| Outlook | `smtp-mail.outlook.com` | 587 | Use an App Password |

For non-QQ providers, also add these secrets: `MAIL_SERVER` and `MAIL_PORT`.

---

## Customizing the keywords

Edit the `KEYWORDS` list in [`digest.py`](digest.py) (around line 45) to match your interests. The default is chemistry-focused:

```python
KEYWORDS = [
    "organic synthesis", "total synthesis", "reaction mechanism",
    "catalysis", "medicinal chemistry", "DNA-encoded library",
    "C-H activation", "cross-coupling", "drug discovery",
]
```

Want biology, ML, or physics instead? Just swap the keywords. Each keyword searches `[Title/Abstract]` on PubMed, combined with `OR`.

---

## Tech stack

- **Python 3.11** + `requests`
- **PubMed E-utilities** (free, no API key)
- **DeepSeek Chat** (or any OpenAI-compatible LLM)
- **GitHub Actions** (scheduled + manual trigger)

---

## License

MIT
