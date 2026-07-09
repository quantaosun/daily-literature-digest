# Daily Literature Digest

📬 **Automatically search PubMed → summarize with AI → email digest daily**

---

## Quick Start

👉 **[Follow SETUP.md](SETUP.md)** for step-by-step setup (5 minutes, no coding needed)

---

## What it does

1. Searches PubMed for papers matching your keywords (daily)
2. Summarizes each paper with AI 
3. Emails you a beautiful digest with scores

---

## Setup (TL;DR)

1. Fork this repo
2. Add 3 GitHub Secrets: `LLM_API_KEY`, `MAIL`, `MAIL_PW`
3. Edit `config.yaml` with your keywords
4. Done! Runs daily at 9 AM Beijing time

---

## Customize

Edit `config.yaml`:
```yaml
keywords:
  - your keywords here
  
search_days: 60        # How far back to search
max_papers: 8          # Target number of papers
min_papers: 2          # Minimum to guarantee
```

---

## Email Setup

- **QQ Mail**: [Enable POP3/SMTP](https://service.mail.qq.com/detail/0/75), get 16-char code
- **Gmail**: Create [App Password](https://support.google.com/accounts/answer/185833)
- **163 Mail**: Similar to QQ
- Others: Check your provider's SMTP docs

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| No papers found | Edit keywords in `config.yaml`, increase `search_days` |
| Email not received | Check SPAM folder, verify credentials in GitHub Secrets |
| API error | Check DeepSeek account has credits, verify API key |
| Want to stop | Go to Actions → disable workflow |

---

## Cost

~$0.03/month for AI summaries (DeepSeek)

---

## License

MIT

