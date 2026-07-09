# 🚀 Setup Guide — Daily Literature Digest

> **No coding experience needed!** Follow these steps to set up automatic daily digests.

---

## What You'll Need (3 things)

1. **GitHub Account** (free) — to fork and host the automation
2. **DeepSeek API Key** (free/cheap) — to summarize papers with AI
3. **Email Address** (any provider) — to receive the digest

**Total cost:** ~$0.03/month for the AI summaries.

---

## Step 1️⃣: Fork this repo

**What:** Create your own copy of this project

1. Go to https://github.com/quantaosun/daily-literature-digest
2. Click **Fork** (top-right corner)
3. GitHub will create a copy in your account

✅ **Done.** You now have your own copy.

---

## Step 2️⃣: Customize your keywords

**What:** Tell the system which research topics you care about

### Option A: Using the GitHub Web Editor (Easiest)

1. Go to your forked repo (it should be at `github.com/YOUR_USERNAME/daily-literature-digest`)
2. Click on **config.yaml** file
3. Click the ✏️ **Edit** button
4. **Change the keywords** under `keywords:` — add one per line
   - Delete ones you don't want
   - Add new ones you care about
   - Examples: `machine learning`, `quantum computing`, `climate modeling`

5. Click **Commit changes** (green button) → add a message like "Updated keywords"

### Option B: Customize search range (optional)

In the same `config.yaml` file, you can change:
- `search_days: 60` — How far back to search (1-365 days)
- `max_papers: 8` — Target number of papers per digest
- `min_papers: 2` — Minimum papers before trying harder (ensures at least 2)

✅ **Done.** Your keywords are set!

---

## Step 3️⃣: Get your API keys

### 3a. DeepSeek API Key (for AI summaries)

1. Go to https://platform.deepseek.com
2. Sign up (free account)
3. Go to **API Keys** (left sidebar)
4. Click **Create New Secret Key**
5. Copy the key (it will look like `sk-...`)
6. **Keep this safe** — don't share it

### 3b. Email Credentials

**If using QQ Mail (Recommended for China):**
1. Go to https://mail.qq.com
2. Sign in to your account
3. Click ⚙️ **Settings** → **Account** → **POP3/SMTP/IMAP**
4. Under "POP3/SMTP Service", click **Enable**
5. Answer the security question
6. You'll get a **16-character authorization code** (not your password)
7. Save this code

**If using Gmail:**
1. Go to https://support.google.com/accounts/answer/185833
2. Follow steps to create an **App Password**
3. Save this password

**If using 163 Mail:**
1. Similar to QQ Mail — enable POP3/SMTP and get the auth code

---

## Step 4️⃣: Add Secrets to GitHub

**What:** Store your API keys securely (GitHub will hide them)

1. Go to your forked repo
2. Click **Settings** (top menu) → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add these:

| Secret Name | What to paste |
|------------|--------------|
| `LLM_API_KEY` | Your DeepSeek API key from Step 3a |
| `MAIL` | Your email address (e.g., `yourname@qq.com`) |
| `MAIL_PW` | Your authorization code from Step 3b |

For each one:
- Click **New repository secret**
- Paste the name exactly as shown
- Paste the value
- Click **Add secret**

✅ **Done.** Your secrets are stored safely.

---

## Step 5️⃣: (Optional) Custom email provider

If **not** using QQ Mail, also add these secrets:

| Secret Name | Example |
|------------|---------|
| `MAIL_SERVER` | `smtp.163.com` (for 163), `smtp.gmail.com` (for Gmail), `smtp-mail.outlook.com` (Outlook) |
| `MAIL_PORT` | `465` (for 163) or `587` (for Gmail/Outlook) |

---

## Step 6️⃣: Test it!

**Run your first digest manually:**

1. Go to your forked repo
2. Click **Actions** (top menu)
3. Click **Daily Literature Digest** (left sidebar)
4. Click **Run workflow** → **Run workflow** button
5. Wait 1-2 minutes...
6. Check your email! 📧

If it worked:
- ✅ You'll receive an email with paper summaries
- ✅ The digest shows paper titles, why they matter, and AI scores

If it didn't work:
- Go back to Actions, click the failed run, click **Run digest** job
- Scroll down to see error messages
- Common issues:
  - `LLM_API_KEY not set` → You forgot Step 3a or 4
  - `SMTP failed` → Wrong email/password or need to enable POP3/SMTP
  - `No papers found` → Try changing keywords in `config.yaml`

---

## Step 7️⃣: Done! Automatic runs

Your digest will now run **automatically every day at 9:00 AM Beijing time**.

To **change the schedule**, edit `.github/workflows/daily-digest.yml`:
- Find the line `- cron: '0 1 * * *'` (around line 6)
- Change `0` to your desired hour (UTC):
  - For 12:00 PM UTC: `0 12 * * *`
  - For 6:00 PM Beijing time (UTC+8): `0 10 * * *`

---

## 🎯 Next Steps

### Customize even more:

- **Edit keywords** in `config.yaml` anytime — changes apply to the next run
- **Run manually** from Actions → Run workflow whenever you want
- **Check run history** in Actions tab to see past digests and debug

### Troubleshooting:

| Problem | Solution |
|---------|----------|
| No papers found | Add more keywords or increase `search_days` in `config.yaml` |
| Email not received | Check SPAM folder; verify `MAIL_PW` is correct in secrets |
| API error | Check your DeepSeek account has credits; verify key is correct |
| Want to stop | Go to Actions → disable the scheduled workflow |

---

## 📚 Resources

- **PubMed:** https://pubmed.ncbi.nlm.nih.gov/ — search papers manually
- **DeepSeek Pricing:** https://platform.deepseek.com/pricing — see costs
- **GitHub Actions Docs:** https://docs.github.com/en/actions — learn more

---

## Questions?

Check the **README.md** for more technical details, or open an Issue in the repo!
