#!/usr/bin/env python3
"""
daily-literature-digest
=======================
Searches PubMed for latest chemistry papers matching your keywords,
summarizes them via DeepSeek LLM, and emails the digest to yourself.

Configure via environment variables (set in GitHub Secrets):
  LLM_API_KEY     - DeepSeek or OpenAI-compatible API key (required)
  LLM_BASE_URL    - API base URL (default: https://api.deepseek.com)
  LLM_MODEL       - Model name (default: deepseek-chat)
  MAIL            - Your email address (used as both sender and recipient)
  MAIL_PW         - SMTP password or app-specific password
  MAIL_SERVER     - SMTP server (default: smtp.qq.com)
  MAIL_PORT       - SMTP port (default: 465)
  MAX_PAPERS      - Max papers to fetch per run (default: 8)
"""

import os
import sys
import smtplib
import email.utils
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from xml.etree import ElementTree

import requests

# ── Configuration ──────────────────────────────────────────────────────

LLM_API_KEY    = os.environ.get("LLM_API_KEY")
LLM_BASE_URL   = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com")
LLM_MODEL      = os.environ.get("LLM_MODEL", "deepseek-chat")

SMTP_SERVER    = os.environ.get("MAIL_SERVER", "smtp.qq.com")
SMTP_PORT      = int(os.environ.get("MAIL_PORT", "465"))
SMTP_USER      = os.environ.get("MAIL")
SMTP_PASSWORD  = os.environ.get("MAIL_PW")

MAX_PAPERS     = int(os.environ.get("MAX_PAPERS", "8"))

# ── Search keywords ────────────────────────────────────────────────────
# These are combined with OR and searched in Title/Abstract on PubMed
KEYWORDS = [
    "organic synthesis",
    "total synthesis",
    "reaction mechanism",
    "catalysis",
    "medicinal chemistry",
    "DNA-encoded library",
    "DEL",
    "C-H activation",
    "cross-coupling",
    "enantioselective",
    "organocatalysis",
    "photocatalysis",
    "drug discovery",
]

# ── Helpers ────────────────────────────────────────────────────────────

def log(msg):
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] {msg}")

def truncate_abstract(abstract, max_words=150):
    if not abstract:
        return "No abstract available"
    words = abstract.split()
    if len(words) > max_words:
        return " ".join(words[:max_words]) + "..."
    return abstract

# ── PubMed fetcher ─────────────────────────────────────────────────────

def fetch_pubmed():
    """
    Search PubMed for recent papers matching keywords.
    Uses NCBI E-utilities (no API key required for basic use).
    """
    today = datetime.now()
    # Search papers from last 60 days (wider window = more results)
    start_date = today - timedelta(days=60)
    date_query = '(' + f'"{start_date.strftime("%Y/%m/%d")}"[PDAT] : "{today.strftime("%Y/%m/%d")}"[PDAT]' + ')'

    # Build keyword query: ("keyword1"[Title/Abstract] OR "keyword2"[Title/Abstract] ...)
    keyword_query = '(' + ' OR '.join(f'"{kw}"[Title/Abstract]' for kw in KEYWORDS) + ')'

    full_query = f'{keyword_query} AND {date_query}'

    log(f"Searching PubMed (past 60 days)...")

    # Step 1: Search for IDs
    search_params = {
        "db": "pubmed",
        "term": full_query,
        "retmode": "xml",
        "retmax": str(MAX_PAPERS),
        "sort": "date_desc",
    }

    try:
        resp = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params=search_params,
            timeout=30,
            headers={"User-Agent": "DailyLitDigest/1.0"},
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        log(f"  ⚠  PubMed search failed: {e}")
        return []

    root = ElementTree.fromstring(resp.content)
    id_list = [id_elem.text for id_elem in root.findall(".//Id")]

    if not id_list:
        log("  No papers found in the last 60 days")
        return []

    log(f"  Found {len(id_list)} papers (first: {id_list[0]})")

    # Step 2: Fetch details for each paper
    papers = []
    for pmid in id_list:
        try:
            # Get summary (title, journal, date)
            summary_resp = requests.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                params={"db": "pubmed", "id": pmid, "retmode": "xml"},
                timeout=30,
                headers={"User-Agent": "DailyLitDigest/1.0"},
            )
            summary_resp.raise_for_status()
            summary_root = ElementTree.fromstring(summary_resp.content)

            title = summary_root.findtext('.//Item[@Name="Title"]')
            if not title:
                continue

            journal = summary_root.findtext('.//Item[@Name="Source"]', "Unknown")
            pub_date = summary_root.findtext('.//Item[@Name="PubDate"]', "")

            # Get abstract
            abstract_text = None
            try:
                abstract_resp = requests.get(
                    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
                    params={"db": "pubmed", "id": pmid, "retmode": "xml"},
                    timeout=30,
                    headers={"User-Agent": "DailyLitDigest/1.0"},
                )
                abstract_resp.raise_for_status()
                abstract_root = ElementTree.fromstring(abstract_resp.content)
                abstract_text = abstract_root.findtext('.//AbstractText')
            except Exception as e:
                log(f"  ⚠  Failed to fetch abstract for PMID {pmid}: {e}")

            papers.append({
                "title": title.strip(),
                "journal": journal.strip(),
                "date": pub_date.strip(),
                "abstract": truncate_abstract(abstract_text),
                "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "pmid": pmid,
            })

        except requests.RequestException as e:
            log(f"  ⚠  Failed to fetch details for PMID {pmid}: {e}")
            continue

    return papers

# ── LLM summarization ──────────────────────────────────────────────────

def summarize_with_llm(papers):
    """Send papers to DeepSeek/LLM for summarization. Returns markdown digest."""
    if not papers:
        return "No papers found today."

    papers_text = ""
    for i, p in enumerate(papers, 1):
        papers_text += f"""
--- Paper {i} ---
Title: {p['title']}
Journal: {p['journal']}
Published: {p['date']}
Link: {p['link']}
Abstract: {p['abstract']}
"""

    system_prompt = """You are a chemistry research assistant. Generate a daily literature digest in ENGLISH.

For each paper, provide:
1. **Title** (linked)
2. **Why this matters** — 1-2 sentences on significance
3. **Key contribution** — 2-3 sentences summarizing the main finding
4. **Relevance** — area (organic synthesis, total synthesis, reaction mechanism, medicinal chemistry, DEL, catalysis, etc.)

Format in clean Markdown. End with a "Quick Take" section — overall assessment."""

    user_prompt = f"Here are today's papers from PubMed. Generate a digest.\n\n{papers_text}"

    log(f"Sending {len(papers)} papers to LLM ({LLM_MODEL}) for summarization...")

    try:
        resp = requests.post(
            f"{LLM_BASE_URL.rstrip('/')}/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {LLM_API_KEY}",
            },
            json={
                "model": LLM_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 4096,
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        log("  LLM summarization complete")
        return content
    except Exception as e:
        log(f"  ⚠  LLM API error: {e}")
        return fallback_digest(papers)


def fallback_digest(papers):
    """Generate a simple digest without LLM."""
    lines = [f"**{datetime.now():%B %d, %Y}**\n"]
    for p in papers:
        lines.append(f"## {p['title']}")
        lines.append(f"*{p['journal']}* | {p['date']}")
        lines.append(f"**Link:** {p['link']}")
        lines.append(f"\n{p['abstract']}\n")
    return "\n".join(lines)

# ── HTML email template ──────────────────────────────────────────────

def markdown_to_html(md):
    """Convert basic markdown (headings, bold, links, bare URLs, lists) to HTML."""
    import re
    lines = md.split("\n")
    html_lines = []
    in_list = False

    def inline(line):
        line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
        line = re.sub(r'\*(.+?)\*', r'<em>\1</em>', line)
        line = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', line)
        # Bare URLs (but not already-quoted hrefs)
        line = re.sub(r'(?<!")(https?://[^\s<]+)', r'<a href="\1">\1</a>', line)
        return line

    for line in lines:
        if line.startswith("### "):
            html_lines.append(f"<h3>{inline(line[4:])}</h3>")
        elif line.startswith("## "):
            html_lines.append(f"<h2>{inline(line[3:])}</h2>")
        elif line.startswith("# "):
            html_lines.append(f"<h1>{inline(line[2:])}</h1>")
        elif line.strip() == "---":
            html_lines.append("<hr>")
        elif line.startswith("- "):
            if not in_list:
                in_list = True
                html_lines.append("<ul>")
            html_lines.append(f"<li>{inline(line[2:])}</li>")
        elif not line.strip():
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append("")
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<p>{inline(line)}</p>")

    if in_list:
        html_lines.append("</ul>")

    return "\n".join(html_lines)


def build_html_email(digest_md):
    """Wrap digest content in a styled HTML email with dark mode support."""
    body_html = markdown_to_html(digest_md)
    today = datetime.now().strftime("%B %d, %Y")

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="color-scheme" content="light dark">
<meta name="supported-color-schemes" content="light dark">
<style>
  :root {{
    --bg: #ffffff;
    --bg-card: #f5f6f8;
    --text: #1a1a2e;
    --text-secondary: #555;
    --accent: #2563eb;
    --border: #e2e4e8;
    --hr: #e2e4e8;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg: #0f172a;
      --bg-card: #1e293b;
      --text: #e2e8f0;
      --text-secondary: #94a3b8;
      --accent: #60a5fa;
      --border: #334155;
      --hr: #334155;
    }}
  }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    max-width: 680px;
    margin: 0 auto;
    padding: 24px 16px;
    line-height: 1.6;
    font-size: 15px;
  }}
  h1 {{
    font-size: 24px;
    margin: 0 0 4px 0;
    color: var(--text);
  }}
  h2 {{
    font-size: 18px;
    margin: 28px 0 8px 0;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--border);
    color: var(--text);
  }}
  h3 {{
    font-size: 16px;
    margin: 20px 0 6px 0;
    color: var(--text);
  }}
  p {{
    margin: 6px 0;
  }}
  a {{
    color: var(--accent);
    text-decoration: none;
  }}
  a:hover {{
    text-decoration: underline;
  }}
  hr {{
    border: none;
    border-top: 1px solid var(--hr);
    margin: 24px 0;
  }}
  ul {{
    margin: 6px 0;
    padding-left: 20px;
  }}
  li {{
    margin: 3px 0;
  }}
  .header {{
    margin-bottom: 24px;
  }}
  .header .date {{
    font-size: 13px;
    color: var(--text-secondary);
  }}
  .footer {{
    margin-top: 32px;
    padding-top: 16px;
    border-top: 1px solid var(--border);
    font-size: 12px;
    color: var(--text-secondary);
    text-align: center;
  }}
  @media only screen and (max-width: 480px) {{
    body {{ padding: 16px 12px; }}
    .paper {{ padding: 12px 14px; }}
  }}
</style>
</head>
<body>
  <div class="header">
    <h1>📬 Daily Literature Digest</h1>
    <div class="date">{today}</div>
  </div>
  {body_html}
  <div class="footer">
    Generated by <a href="https://github.com/quantaosun/daily-literature-digest">daily-literature-digest</a>
  </div>
</body>
</html>"""


# ── Email sending ────────────────────────────────────────────────────

def send_email(digest_md):
    """Send the digest via SMTP. Sends to yourself."""
    if not all([SMTP_SERVER, SMTP_USER, SMTP_PASSWORD]):
        log("⚠  SMTP not fully configured, printing digest instead")
        print(digest_md)
        return

    today = datetime.now().strftime("%Y-%m-%d")
    subject = f"Daily Literature Digest — {today}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = SMTP_USER
    msg["Date"] = email.utils.formatdate(localtime=True)

    msg.attach(MIMEText(digest_md, "plain", "utf-8"))
    msg.attach(MIMEText(build_html_email(digest_md), "html", "utf-8"))

    try:
        log(f"Connecting to {SMTP_SERVER}:{SMTP_PORT}...")
        if SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=30)
        else:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30)
            server.starttls()

        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, [SMTP_USER], msg.as_string())
        server.quit()
        log(f"✅ Email sent to {SMTP_USER}")
    except Exception as e:
        log(f"⚠  Failed to send email: {e}")
        print("\n=== DIGEST (email failed) ===")
        print(digest_md)

# ── Main ───────────────────────────────────────────────────────────────

def main():
    log("Starting daily literature digest...")

    if not LLM_API_KEY:
        log("⚠  LLM_API_KEY not set. Set it up in GitHub Secrets.")
        sys.exit(1)

    papers = fetch_pubmed()

    if not papers:
        log("No papers found.")
        send_email("# Daily Literature Digest\n\nNo papers found matching your criteria today.")
        return

    log(f"Total papers: {len(papers)}")

    digest = summarize_with_llm(papers)

    send_email(digest)

    print(digest)
    log("✅ Done!")


if __name__ == "__main__":
    main()
