# Daily Literature Digest

> 📬 **Automatically search PubMed → summarize with AI → email the digest to you.**
>
> [🇨🇳 中文版](README.zh.md)

## ⚡ Quick Start (5 minutes)

**For non-coders:** Follow the [SETUP.md](SETUP.md) guide step-by-step.

**For developers:** 
1. Fork this repo
2. Add 3 GitHub Secrets: `LLM_API_KEY`, `MAIL`, `MAIL_PW`
3. Edit `config.yaml` with your keywords
4. Done! Runs daily at 9 AM Beijing time

---

## What is this?

This GitHub Actions workflow **automatically**:
1. **Searches PubMed** for papers matching your research interests (daily)
2. **Summarizes each paper** using AI (DeepSeek LLM)
3. **Scores papers** by novelty, impact, and relevance
4. **Emails you a digest** with beautiful formatting

**No servers to set up. No cron jobs to configure. Just fork and add secrets.**

---

## Why use it?

- ✅ **Stay updated** on new research in your field
- ✅ **Save time** — AI summarizes instead of you reading abstracts
- ✅ **Personalized** — customize keywords to your interests
- ✅ **Free/cheap** — ~$0.03/month for AI summaries
- ✅ **Hands-off** — runs automatically every day

### Example digest email:

```
📬 Daily Literature Digest — 2025-07-09

## Paper 1: Novel C-H Activation Strategy...
📖 Why this matters: This paper introduces a breakthrough in selective C-H activation...
💡 Key contribution: The authors developed...
🔗 Link: https://pubmed.ncbi.nlm.nih.gov/12345678/
```

---

## What is GitHub Actions?

GitHub Actions is a free automation service built into GitHub. Think of it as a robot that:
- Runs your code on a schedule (e.g., daily)
- Or triggers when you click a button
- Can send emails, run tests, deploy code, etc.

**No servers to manage.** GitHub handles everything.

**Cost:** ~$0.03/month on DeepSeek (~4,000 tokens per run, once daily).

---

## How it works

```
Daily schedule (9 AM Beijing)
           ↓
GitHub Actions starts
           ↓
PubMed API (free, no key needed)
Search papers from last 60 days matching your keywords
           ↓
DeepSeek LLM (paid, ~0.03¢ per run)
Summarize each paper & generate scores
           ↓
SMTP (your email provider)
Send beautiful digest to your inbox
```

---

## 📋 Setup (3 minutes)

### For non-coders:
👉 **Follow [SETUP.md](SETUP.md)** — step-by-step guide with screenshots

### For developers:

**1. Fork this repo** (top-right corner)

**2. Add 3 Secrets** → Settings → Secrets and variables → Actions → New repository secret:

| Secret | Value |
|--------|-------|
| `LLM_API_KEY` | Your DeepSeek API key ([platform.deepseek.com](https://platform.deepseek.com)) |
| `MAIL` | Your email address (e.g., `yourname@qq.com`) |
| `MAIL_PW` | Your SMTP password / authorization code |

**3. (Optional) Customize keywords:**

Edit `config.yaml`:
```yaml
keywords:
  - organic synthesis
  - total synthesis
  - catalysis
  # Add your own keywords here
```

**4. Done.** The next scheduled run will send you a digest. Or go to **Actions → Daily Literature Digest → Run workflow** to test immediately.

---

## 📧 Email Setup

### QQ Mail (Recommended)

1. Go to [QQ Mail Settings](https://service.mail.qq.com/detail/0/75)
2. Enable "POP3/SMTP"
3. Get your 16-character authorization code
4. Add GitHub Secrets:
   - `MAIL`: yourname@qq.com
   - `MAIL_PW`: (16-char code)

### Gmail

1. Create an [App Password](https://support.google.com/accounts/answer/185833)
2. Add GitHub Secrets:
   - `MAIL`: youremail@gmail.com
   - `MAIL_PW`: (app password)
   - `MAIL_SERVER`: smtp.gmail.com
   - `MAIL_PORT`: 587

### 163 Mail

Similar to QQ Mail. Enable POP3/SMTP, get the auth code.

Other providers: Outlook, Yahoo, etc. — check their SMTP setup docs.

---

## ⚙️ Configuration

### Via config.yaml (easy)

Edit `config.yaml` to customize:

```yaml
# Search keywords (one per line)
keywords:
  - organic synthesis
  - catalysis
  - drug discovery

# How many days back to search
search_days: 60

# Number of papers to fetch
max_papers: 8

# Minimum papers to guarantee (retries if needed)
min_papers: 2

# Email provider (leave blank for QQ default)
email:
  server: ""      # smtp.163.com, smtp.gmail.com, etc.
  port: ""        # 465 or 587

# LLM provider (leave blank for DeepSeek default)
llm:
  base_url: ""    # https://api.deepseek.com
  model: ""       # deepseek-chat
```

### Via Environment Variables (GitHub Secrets)

Already set in `.github/workflows/daily-digest.yml`:

| Environment | Secret | Default |
|-------------|--------|---------|
| `LLM_API_KEY` | `LLM_API_KEY` | (required) |
| `LLM_BASE_URL` | `LLM_BASE_URL` | https://api.deepseek.com |
| `LLM_MODEL` | `LLM_MODEL` | deepseek-chat |
| `MAIL_SERVER` | `MAIL_SERVER` | smtp.qq.com |
| `MAIL_PORT` | `MAIL_PORT` | 465 |
| `MAIL` | `MAIL` | (required) |
| `MAIL_PW` | `MAIL_PW` | (required) |
| `MAX_PAPERS` | `MAX_PAPERS` | 8 |

---

## 🎯 Features

- ✅ **Automatic daily runs** (configurable schedule)
- ✅ **AI-powered summaries** with novelty/impact scoring
- ✅ **Beautiful HTML emails** with dark mode support
- ✅ **Retry logic** — ensures minimum 2 papers even if search finds fewer
- ✅ **Custom keywords** — edit config.yaml without coding
- ✅ **Manual trigger** — run anytime from GitHub Actions UI
- ✅ **Error handling** — graceful fallback if LLM unavailable

---

## 🔧 Troubleshooting

### No papers found

1. **Edit keywords** in `config.yaml` — PubMed may not have papers for your terms
2. **Increase `search_days`** — search older papers (1-365 days)
3. **Test on PubMed** — go to https://pubmed.ncbi.nlm.nih.gov/ and search manually
4. Check your keywords match the literature you expect

### Email not received

1. **Check SPAM** — emails sometimes land there
2. **Verify email credentials** in GitHub Secrets
3. **Check Auth Code** — for QQ/163, make sure you used the 16-char code (not your password)
4. **Go to Actions tab** → failed run → see error logs

### API error (LLM)

1. **Check DeepSeek account** — ensure you have credits
2. **Verify API key** is correct in GitHub Secrets
3. **Check rate limits** — DeepSeek free tier has limits

### Want to stop automated runs?

Go to **Actions** → **Daily Literature Digest** → click **⋯** (more) → **Disable workflow**

---

## 📚 Tech Stack

- **Python 3.11** + `requests`
- **PubMed E-utilities** (free, no API key needed)
- **DeepSeek Chat** (or any OpenAI-compatible LLM)
- **GitHub Actions** (scheduled + manual trigger)
- **YAML config** (easy editing for non-coders)

---

## 🔍 How to change the daily schedule

Edit `.github/workflows/daily-digest.yml` (line 6):

```yaml
- cron: '0 1 * * *'  # Current: 1 AM UTC = 9 AM Beijing
```

Change the first `0` (hour in UTC 0-23):
- `0 1 * * *` → 1 AM UTC (9 AM Beijing)
- `0 12 * * *` → 12 PM UTC (8 PM Beijing)
- `0 10 * * *` → 10 AM UTC (6 PM Beijing)

[Cron syntax help](https://crontab.guru/)

---

## 🚀 Limitations

- **PubMed only** — searches PubMed, which is a subset of biomedical literature
- **Open abstracts** — papers behind paywalls may have no/truncated abstracts
- **Rate limits** — PubMed free API has rate limits (respected by this script)
- **English output** — digest is in English only

---

## 🤝 Contributing

Found a bug? Have a feature request? Open an issue or submit a PR!

---

## 📄 License

MIT

---

## 🙋 Questions?

1. Check [SETUP.md](SETUP.md) for step-by-step non-coder guide
2. Check this README for more technical details
3. Open an issue in this repo

