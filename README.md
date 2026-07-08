# Daily Literature Digest

Automatically search PubMed for latest chemistry papers, summarize them with DeepSeek LLM, and email yourself a daily digest — all for free via GitHub Actions.

**Tracked topics:** organic synthesis, total synthesis, reaction mechanism, catalysis, medicinal chemistry, DNA-encoded library (DEL), C-H activation, cross-coupling, enantioselective, organocatalysis, photocatalysis, drug discovery

**Data source:** PubMed (NCBI E-utilities, free, no API key required)

**Cost:** GitHub Actions (free) + DeepSeek API (~¥0.01/day)

---

## Quick Start

### 1. Fork this repo

Click the **Fork** button on GitHub to create your own copy.

### 2. Get a DeepSeek API Key

Go to [platform.deepseek.com](https://platform.deepseek.com) → Register → Create API Key. Copy the key (starts with `sk-...`).

### 3. Get your email SMTP password

See [Email Setup](#email-setup) below for your email provider.

### 4. Add 3 Secrets

Go to your forked repo → **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret | Your value |
|--------|-----------|
| `LLM_API_KEY` | DeepSeek API Key (`sk-...`) |
| `MAIL` | Your email address (e.g. `yourname@qq.com`) |
| `MAIL_PW` | SMTP password / authorization code (see below) |

That's all you need. The defaults work for QQ Mail. If you use a different provider, also set `MAIL_SERVER` and `MAIL_PORT` (see the table below).

### 5. Run it

Go to **Actions → Daily Literature Digest → Run workflow**. The first email should arrive in a few minutes.

After that, it runs automatically every day at **9:00 AM Beijing Time (1:00 UTC)**.

---

## Email Setup

### QQ Mail（最常用）

QQ Mail is the most popular email provider in China and works best with this project. Here's how to set it up:

**Step 1: Get your SMTP authorization code**

<details>
<summary>📱 Open this for step-by-step instructions</summary>

1. **Login** to [mail.qq.com](https://mail.qq.com) with your QQ account
2. **Go to Settings**: Click the gear icon ⚙️ in the top-right corner
3. **Select "Account" tab**: It's in the left sidebar (not the "General" tab)
4. **Scroll down** to find **"POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV service"**
5. Click **"Enable"** next to **"POP3/SMTP service"**
6. **Verify via SMS**: Send the required text message to the number shown (usually `1069070069`)
7. **Copy the authorization code**: After verification, you'll get a **16-character code** (e.g. `abcdefghijklmnop`)

> ⚠️ **Important:** The code is shown only once! Copy it immediately and save it somewhere safe. If you lose it, you'll need to disable and re-enable the service to get a new one.

</details>

**Step 2: Add these to GitHub Secrets**

| Secret | Value |
|--------|-------|
| `MAIL` | Your full QQ email address (e.g. `123456789@qq.com`) |
| `MAIL_PW` | The 16-character authorization code from Step 1 |

You don't need to set `MAIL_SERVER` or `MAIL_PORT` — they default to `smtp.qq.com:465`.

**Step 3: Test it**

Go to **Actions → Daily Literature Digest → Run workflow**. Check your QQ Mail inbox (and spam folder) in a few minutes.

---

### Other Email Providers

<details>
<summary>Click to expand</summary>

| Provider | SMTP Server | Port | How to get password |
|----------|-------------|------|-------------------|
| **QQ Mail** | `smtp.qq.com` | 465 | Settings → Account → Enable POP3/SMTP → Get authorization code |
| **163 Mail** | `smtp.163.com` | 465 | Settings → POP3/SMTP/IMAP → Enable → Get authorization code |
| **Gmail** | `smtp.gmail.com` | 587 | Google Account → Security → App passwords → Generate |
| **Outlook** | `smtp-mail.outlook.com` | 587 | Account settings → Security → App password |

If using a non-QQ provider, add two more secrets:
| Secret | Value |
|--------|-------|
| `MAIL_SERVER` | Your provider's SMTP server (e.g. `smtp.163.com`) |
| `MAIL_PORT` | SMTP port (e.g. `465` for SSL, `587` for TLS) |

</details>

---

## Customize Keywords

Edit `KEYWORDS` in `digest.py` (around line 47):

```python
KEYWORDS = [
    "organic synthesis",
    "total synthesis",
    # add your own:
    "your keyword here",
    # or remove ones you don't need
]
```

Then commit and push. The next run will use your new keywords.

---

## How It Works

```
PubMed API (free, no key needed)
       ↓
Search papers from last 60 days matching your keywords
       ↓
Summarize each paper with DeepSeek LLM (English)
       ↓
Send email digest to yourself via SMTP
```

**Tech stack:** Python 3.11 + `requests` | GitHub Actions | PubMed E-utilities | DeepSeek API

---

## Troubleshooting

<details>
<summary>I'm not receiving emails</summary>

- Check your **spam folder**
- Verify `MAIL` and `MAIL_PW` secrets are set correctly in GitHub
- For QQ Mail: make sure you used the **authorization code**, not your QQ password
- Go to Actions → click the latest run → check the logs for errors
</details>

<details>
<summary>Only 1 paper found</summary>

PubMed updates daily. Some days have fewer matching papers. You can:
- Widen the search window: edit `timedelta(days=60)` in `fetch_pubmed()`
- Add more keywords to `KEYWORDS`
- Increase `MAX_PAPERS` (default 8)
</details>

<details>
<summary>I want to change how often it runs</summary>

Edit the `cron` expression in `.github/workflows/daily-digest.yml`:

```yaml
on:
  schedule:
    - cron: '0 1 * * *'   # Change this
```
Use [crontab.guru](https://crontab.guru) to generate your own schedule.
</details>

---

## License

MIT
