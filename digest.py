#!/usr/bin/env python3
"""
daily-literature-digest
=======================
Searches PubMed for latest papers matching your keywords,
summarizes them via LLM, scores them by novelty and impact,
and emails the digest with interactive HTML formatting.

Configure via:
  1. Environment variables (set in GitHub Secrets)
  2. config.yaml file (edit directly for keywords/settings)
"""

import os
import sys
import smtplib
import email.utils
import json
import base64
import yaml
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from xml.etree import ElementTree

import requests

# ── Load configuration ──────────────────────────────────────────────────

def load_config():
    """Load configuration from config.yaml or use defaults."""
    config_file = "config.yaml"
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            log(f"⚠  Failed to load config.yaml: {e}, using defaults")
            return {}
    return {}

CONFIG = load_config()

# ── Environment + Config merged settings ────────────────────────────────

LLM_API_KEY    = os.environ.get("LLM_API_KEY")
LLM_BASE_URL   = os.environ.get("LLM_BASE_URL") or \
                 CONFIG.get("llm", {}).get("base_url") or \
                 "https://api.deepseek.com"
LLM_MODEL      = os.environ.get("LLM_MODEL") or \
                 CONFIG.get("llm", {}).get("model") or \
                 "deepseek-chat"

SMTP_SERVER    = os.environ.get("MAIL_SERVER") or \
                 CONFIG.get("email", {}).get("server") or \
                 "smtp.qq.com"
SMTP_PORT      = int(os.environ.get("MAIL_PORT") or \
                     CONFIG.get("email", {}).get("port") or \
                     "465")
SMTP_USER      = os.environ.get("MAIL")
SMTP_PASSWORD  = os.environ.get("MAIL_PW")

MAX_PAPERS     = int(os.environ.get("MAX_PAPERS") or \
                    CONFIG.get("max_papers") or "8")
MIN_PAPERS     = int(CONFIG.get("min_papers") or "2")
SEARCH_DAYS    = int(CONFIG.get("search_days") or "60")

# ── Search keywords from config.yaml ────────────────────────────────────
KEYWORDS = CONFIG.get("keywords", [
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
])

# ── Helpers ───────────────────────────────────────────────────────────

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

def fetch_pubmed(days_back=None, attempt=1):
    """
    Search PubMed for recent papers matching keywords with retry logic.
    Uses NCBI E-utilities (no API key required for basic use).
    
    If fewer than MIN_PAPERS are found, retries with a wider date range.
    """
    if days_back is None:
        days_back = SEARCH_DAYS
    
    today = datetime.now()
    start_date = today - timedelta(days=days_back)
    date_query = '(' + f'"{start_date.strftime("%Y/%m/%d")}"[PDAT] : "{today.strftime("%Y/%m/%d")}"[PDAT]' + ')'

    # Build keyword query: ("keyword1"[Title/Abstract] OR "keyword2"[Title/Abstract] ...)
    keyword_query = '(' + ' OR '.join(f'"{kw}"[Title/Abstract]' for kw in KEYWORDS) + ')'

    full_query = f'{keyword_query} AND {date_query}'

    log(f"Searching PubMed (past {days_back} days)...")

    # Step 1: Search for IDs
    search_params = {
        "db": "pubmed",
        "term": full_query,
        "retmode": "xml",
        "retmax": str(MAX_PAPERS * 2),  # Fetch more IDs to account for papers without abstracts
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
        log(f"  No papers found in the last {days_back} days")
        # Retry with wider date range if we haven't tried yet
        if attempt < 3 and days_back < 365:
            log(f"  Retrying with wider date range ({days_back * 2} days)...")
            return fetch_pubmed(days_back=days_back * 2, attempt=attempt + 1)
        return []

    log(f"  Found {len(id_list)} papers")

    # Step 2: Fetch details for each paper
    papers = []
    for pmid in id_list:
        if len(papers) >= MAX_PAPERS:
            break
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
                "full_abstract": abstract_text or "No abstract available",
                "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "pmid": pmid,
            })

        except requests.RequestException as e:
            log(f"  ⚠  Failed to fetch details for PMID {pmid}: {e}")
            continue

    return papers

# ── LLM summarization with scoring ──────────────────────────────────────

def analyze_and_score_papers(papers):
    """
    Send papers to LLM for detailed analysis and scoring.
    Returns: (digest_markdown, scored_papers_list)
    """
    if not papers:
        return "No papers found today.", []

    papers_text = ""
    for i, p in enumerate(papers, 1):
        papers_text += f"""
--- Paper {i} ---
Title: {p['title']}
Journal: {p['journal']}
Published: {p['date']}
Link: {p['link']}
Abstract: {p['full_abstract']}
"""

    system_prompt = """You are a chemistry research analyst. Analyze these papers and provide:

1. A detailed markdown digest with sections for each paper including:
   - **Title** — with clickable PubMed link in markdown format [Title](link)
   - **Link** — always include the PubMed link as [View on PubMed](link)
   - **Why this matters** — significance and novelty
   - **Key contribution** — 2-3 sentences of main finding
   - **Relevance** — research area
   - **Trend connection** — how this connects to recent science trends

IMPORTANT: Every paper MUST include its PubMed link in the format:
[View on PubMed](https://pubmed.ncbi.nlm.nih.gov/PMID/)

2. A scoring summary (JSON format at the end) with each paper scored 1-10 on:
   - novelty (how novel/innovative)
   - impact (potential significance)
   - trend_relevance (connection to current chemistry trends)

Format the JSON as:
```json
{
  "paper_scores": [
   {"title": "...", "novelty": N, "impact": N, "trend_relevance": N, "overall": N}
  ],
  "trend_insights": "Brief summary of detected science trends"
}
```

End with a "Quick Take" section — overall assessment.

MANDATORY: Include clickable links for every paper."""

    user_prompt = f"""Here are today's papers from PubMed. Provide detailed analysis with scoring.

{papers_text}

Remember to include the JSON scoring at the end."""

    log(f"Sending {len(papers)} papers to LLM ({LLM_MODEL}) for detailed analysis...")

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
                "max_tokens": 6000,
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        log("  LLM analysis complete")
        
        # Extract scores from JSON
        scored_papers = extract_scores(content, papers)
        return content, scored_papers
    except Exception as e:
        log(f"  ⚠  LLM API error: {e}")
        return fallback_digest(papers), []


def extract_scores(llm_response, papers):
    """Extract paper scores from LLM response JSON."""
    try:
        # Find JSON block in response
        start = llm_response.find("```json")
        end = llm_response.find("```", start + 7)
        if start != -1 and end != -1:
            json_str = llm_response[start + 7:end].strip()
            data = json.loads(json_str)
            return data.get("paper_scores", [])
    except Exception as e:
        log(f"  ⚠  Failed to parse scores: {e}")
    return []


def fallback_digest(papers):
    """Generate a simple digest without advanced LLM analysis."""
    lines = [f"**{datetime.now():%B %d, %Y}**\n"]
    for p in papers:
        lines.append(f"## [{p['title']}]({p['link']})")
        lines.append(f"*{p['journal']}* | {p['date']}")
        lines.append(f"**Link:** {p['link']}")
        lines.append(f"\n{p['abstract']}\n")
    return "\n".join(lines)

# ── HTML email template with interactive elements ──────────────────────

def markdown_to_html(md):
    """Convert markdown to HTML with proper formatting."""
    import re
    lines = md.split("\n")
    html_lines = []
    in_list = False

    def inline(line):
        line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
        line = re.sub(r'\*(.+?)\*', r'<em>\1</em>', line)
        line = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2" target="_blank">\1</a>', line)
        line = re.sub(r'(?<!")(https?://[^\s<]+)', r'<a href="\1" target="_blank">\1</a>', line)
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


def create_score_chart_svg(scored_papers):
    """Create an SVG chart showing paper scores."""
    if not scored_papers or len(scored_papers) == 0:
        return ""
    
    # Limit to top 5 papers
    papers_to_chart = scored_papers[:5]
    
    chart_width = 400
    chart_height = 300
    padding = 40
    bar_width = 50
    bar_gap = 15
    
    svg_lines = [
        f'<svg width="{chart_width}" height="{chart_height}" xmlns="http://www.w3.org/2000/svg">',
        '<style>',
        '.chart-title { font-size: 16px; font-weight: bold; fill: #1a1a2e; }',
        '.chart-label { font-size: 12px; fill: #666; }',
        '.bar-novelty { fill: #3b82f6; }',
        '.bar-impact { fill: #ef4444; }',
        '.bar-trend { fill: #10b981; }',
        '@media (prefers-color-scheme: dark) {',
        '.chart-title { fill: #e2e8f0; }',
        '.chart-label { fill: #94a3b8; }',
        '}',
        '</style>',
    ]
    
    # Title
    svg_lines.append(f'<text x="10" y="25" class="chart-title">Paper Scores (Top 5)</text>')
    
    # Y-axis
    svg_lines.append(f'<line x1="{padding-10}" y1="{padding}" x2="{padding-10}" y2="{chart_height-padding}" stroke="#ccc" stroke-width="1"/>')
    
    # X-axis
    svg_lines.append(f'<line x1="{padding-10}" y1="{chart_height-padding}" x2="{chart_width-padding}" y2="{chart_height-padding}" stroke="#ccc" stroke-width="1"/>')
    
    # Y-axis labels (0, 5, 10)
    for i in [0, 5, 10]:
        y = chart_height - padding - (i/10.0) * (chart_height - 2*padding)
        svg_lines.append(f'<text x="5" y="{y+4}" class="chart-label" text-anchor="end">{i}</text>')
    
    # Bars for each paper
    x_pos = padding
    for idx, paper in enumerate(papers_to_chart):
        novelty = paper.get("novelty", 5)
        impact = paper.get("impact", 5)
        trend = paper.get("trend_relevance", 5)
        
        # Novelty bar
        h1 = (novelty/10.0) * (chart_height - 2*padding)
        svg_lines.append(f'<rect x="{x_pos}" y="{chart_height-padding-h1}" width="{bar_width//3-2}" height="{h1}" class="bar-novelty"/>')
        
        # Impact bar
        h2 = (impact/10.0) * (chart_height - 2*padding)
        svg_lines.append(f'<rect x="{x_pos+bar_width//3}" y="{chart_height-padding-h2}" width="{bar_width//3-2}" height="{h2}" class="bar-impact"/>')
        
        # Trend bar
        h3 = (trend/10.0) * (chart_height - 2*padding)
        svg_lines.append(f'<rect x="{x_pos+2*bar_width//3}" y="{chart_height-padding-h3}" width="{bar_width//3-2}" height="{h3}" class="bar-trend"/>')
        
        x_pos += bar_width + bar_gap
    
    # Legend
    legend_y = chart_height - 10
    svg_lines.append(f'<rect x="{padding}" y="{legend_y-15}" width="10" height="10" class="bar-novelty"/>')
    svg_lines.append(f'<text x="{padding+15}" y="{legend_y-5}" class="chart-label">Novelty</text>')
    
    svg_lines.append(f'<rect x="{padding+100}" y="{legend_y-15}" width="10" height="10" class="bar-impact"/>')
    svg_lines.append(f'<text x="{padding+115}" y="{legend_y-5}" class="chart-label">Impact</text>')
    
    svg_lines.append(f'<rect x="{padding+180}" y="{legend_y-15}" width="10" height="10" class="bar-trend"/>')
    svg_lines.append(f'<text x="{padding+195}" y="{legend_y-5}" class="chart-label">Trend</text>')
    
    svg_lines.append('</svg>')
    
    return "\n".join(svg_lines)


def build_html_email(digest_md, scored_papers):
    """Wrap digest content in a styled interactive HTML email."""
    body_html = markdown_to_html(digest_md)
    today = datetime.now().strftime("%B %d, %Y")
    
    # Create score chart
    score_chart = create_score_chart_svg(scored_papers)
    chart_section = ""
    if score_chart:
        chart_section = f"""
    <div class="section">
      <h2>📊 Paper Scores Overview</h2>
      <div class="chart-container">
        {score_chart}
      </div>
      <p class="chart-note"><em>Bars show novelty (blue), impact (red), and trend relevance (green)</em></p>
    </div>
"""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
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
  * {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Helvetica, Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    max-width: 720px;
    margin: 0 auto;
    padding: 20px 16px;
    line-height: 1.7;
    font-size: 15px;
  }}
  .container {{
    background: var(--bg-card);
    border-radius: 8px;
    padding: 24px;
    margin: 0;
  }}
  h1 {{
    font-size: 28px;
    margin: 0 0 8px 0;
    color: var(--text);
  }}
  .date {{
    font-size: 13px;
    color: var(--text-secondary);
    margin-bottom: 24px;
  }}
  h2 {{
    font-size: 20px;
    margin: 28px 0 12px 0;
    padding-bottom: 8px;
    border-bottom: 2px solid var(--accent);
    color: var(--text);
  }}
  h3 {{
    font-size: 17px;
    margin: 20px 0 8px 0;
    color: var(--text);
  }}
  p {{
    margin: 12px 0;
  }}
  a {{
    color: var(--accent);
    text-decoration: none;
    transition: opacity 0.2s;
  }}
  a:hover {{
    opacity: 0.8;
    text-decoration: underline;
  }}
  strong {{
    color: var(--text);
    font-weight: 600;
  }}
  em {{
    font-style: italic;
    color: var(--text-secondary);
  }}
  hr {{
    border: none;
    border-top: 1px solid var(--border);
    margin: 24px 0;
  }}
  ul {{
    margin: 8px 0;
    padding-left: 24px;
  }}
  li {{
    margin: 6px 0;
  }}
  .section {{
    margin: 24px 0;
    padding: 16px;
    background: rgba(37, 99, 235, 0.05);
    border-left: 4px solid var(--accent);
    border-radius: 4px;
  }}
  @media (prefers-color-scheme: dark) {{
    .section {{
      background: rgba(96, 165, 250, 0.05);
    }}
  }}
  .chart-container {{
    margin: 16px 0;
    display: flex;
    justify-content: center;
    overflow-x: auto;
  }}
  .chart-note {{
    font-size: 12px;
    color: var(--text-secondary);
    margin-top: 8px;
  }}
  .footer {{
    margin-top: 32px;
    padding-top: 16px;
    border-top: 1px solid var(--border);
    font-size: 12px;
    color: var(--text-secondary);
    text-align: center;
  }}
  .cta-button {{
    display: inline-block;
    background: var(--accent);
    color: #fff;
    padding: 10px 16px;
    border-radius: 4px;
    text-decoration: none;
    margin-top: 12px;
    transition: opacity 0.2s;
  }}
  .cta-button:hover {{
    opacity: 0.9;
  }}
  @media only screen and (max-width: 480px) {{
    body {{ padding: 16px 12px; }}
    .container {{ padding: 16px; }}
    h1 {{ font-size: 24px; }}
    h2 {{ font-size: 18px; }}
  }}
</style>
</head>
<body>
  <div class="container">
    <h1>📬 Daily Literature Digest</h1>
    <div class="date">{today}</div>
    
{chart_section}
    
    {body_html}
    
    <div class="footer">
      <p>Generated by <a href="https://github.com/quantaosun/daily-literature-digest">daily-literature-digest</a></p>
      <p style="margin-top: 8px; font-size: 11px;">Built with ❤️ for chemistry research</p>
    </div>
  </div>
</body>
</html>"""


# ── Email sending ────────────────────────────────────────────────────

def send_email(digest_md, scored_papers):
    """Send the digest via SMTP with interactive HTML."""
    if not all([SMTP_SERVER, SMTP_USER, SMTP_PASSWORD]):
        log("⚠  SMTP not fully configured, printing digest instead")
        print(digest_md)
        return

    today = datetime.now().strftime("%Y-%m-%d")
    subject = f"📬 Daily Literature Digest — {today}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = SMTP_USER
    msg["Date"] = email.utils.formatdate(localtime=True)

    msg.attach(MIMEText(digest_md, "plain", "utf-8"))
    msg.attach(MIMEText(build_html_email(digest_md, scored_papers), "html", "utf-8"))

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

# ── Main ────────────────────────────────────────────────────────────

def main():
    log("Starting daily literature digest...")

    if not LLM_API_KEY:
        log("⚠  LLM_API_KEY not set. Set it in GitHub Secrets.")
        sys.exit(1)

    papers = fetch_pubmed()

    if len(papers) < MIN_PAPERS:
        if papers:
            log(f"Only {len(papers)} paper(s) found, but MIN_PAPERS is set to {MIN_PAPERS}")
        log(f"No papers found matching your keywords today.")
        if not papers:
            send_email("# 📬 Daily Literature Digest\n\nNo papers found matching your keywords today.\n\n---\n\nTry:\n- Adjusting your search keywords in config.yaml\n- Expanding search_days\n- Checking PubMed directly", [])
        return

    log(f"Total papers: {len(papers)}")

    digest, scored_papers = analyze_and_score_papers(papers)

    send_email(digest, scored_papers)

    print(digest)
    log("✅ Done!")



if __name__ == "__main__":
    main()
