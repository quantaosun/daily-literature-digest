#!/usr/bin/env python3
"""
daily-literature-digest
=======================
Fetches latest papers from arXiv/PubMed matching organic chemistry
keywords, summarizes them via DeepSeek LLM, and emails the digest.

Configure via environment variables (set in GitHub Secrets):
  LLM_API_KEY     - DeepSeek or OpenAI-compatible API key
  LLM_BASE_URL    - API base URL (default: https://api.deepseek.com)
  LLM_MODEL       - Model name (default: deepseek-chat)
  SMTP_USER       - Your email address (used as both sender and recipient)
  SMTP_PASSWORD   - SMTP password or app-specific password
  SMTP_SERVER     - SMTP server (default: smtp.qq.com)
  SMTP_PORT       - SMTP port (default: 465)
  MAX_PAPERS      - Max papers to fetch per run (default: 8)
"""

import os
import sys
import json
import smtplib
import email.utils
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from xml.etree import ElementTree
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError

# ── Configuration ──────────────────────────────────────────────────────

LLM_API_KEY    = os.environ.get("LLM_API_KEY")
LLM_BASE_URL   = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com")
LLM_MODEL      = os.environ.get("LLM_MODEL", "deepseek-chat")

SMTP_SERVER    = os.environ.get("MAIL_SERVER", "smtp.qq.com")
SMTP_PORT      = int(os.environ.get("MAIL_PORT", "465"))
SMTP_USER      = os.environ.get("MAIL")
SMTP_PASSWORD  = os.environ.get("MAIL_PW")

MAX_PAPERS     = int(os.environ.get("MAX_PAPERS", "8"))

# ── Search query ───────────────────────────────────────────────────────
# arXiv search query targeting organic chemistry papers
ARXIV_QUERY = '('.join([
    'cat:chem.OT',  # Organic Chemistry (the main arXiv chemistry category)
    'cat:q-bio.BM', # Biomolecules (for DEL / medicinal chemistry)
    'cat:physics.chem-ph',  # Chemical Physics (for reaction mechanisms)
]) + ') AND ('.join([
    'abs:"organic synthesis"',
    'abs:"total synthesis"',
    'abs:"reaction mechanism"',
    'abs:"catalysis"',
    'abs:"medicinal chemistry"',
    'abs:"DNA-encoded library"',
    'abs:"DEL"',
    'abs:"C-H activation"',
    'abs:"cross-coupling"',
    'abs:"enantioselective"',
    'abs:"organocatalysis"',
    'abs:"photocatalysis"',
    'abs:"drug discovery"',
]) + ')'

PUBMED_QUERY = '('.join([
    '"organic synthesis"[Title/Abstract]',
    '"total synthesis"[Title/Abstract]',
    '"reaction mechanism"[Title/Abstract]',
    '"DNA-encoded library"[Title/Abstract]',
    '"medicinal chemistry"[Title/Abstract]',
    '"drug discovery"[Title/Abstract]',
    '"C-H activation"[Title/Abstract]',
    '"enantioselective"[Title/Abstract]',
    '"organocatalysis"[Title/Abstract]',
]) + ') AND ("2026"[Date - Publication] : "3000"[Date - Publication])'

# ── Helpers ────────────────────────────────────────────────────────────

def log(msg):
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] {msg}")

def fetch_url(url, headers=None):
    req = Request(url, headers=headers or {"User-Agent": "DailyLitDigest/1.0"})
    try:
        with urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except URLError as e:
        log(f"  ⚠  Network error: {e}")
        return None

# ── arXiv fetcher ──────────────────────────────────────────────────────

def fetch_arxiv():
    """
    Fetch recent papers from arXiv using the arXiv API.
    Returns list of dicts: {title, authors, summary, link, published}
    """
    url = (
        "http://export.arxiv.org/api/query?"
        + urlencode({
            "search_query": ARXIV_QUERY,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": MAX_PAPERS,
        })
    )
    log("Fetching arXiv papers...")
    xml_text = fetch_url(url)
    if not xml_text:
        return []

    ns = {"a": "http://www.w3.org/2005/Atom",
          "opensearch": "http://a9.com/-/spec/opensearch/1.1/"}
    root = ElementTree.fromstring(xml_text)
    total = int(root.find(".//opensearch:totalResults", ns).text)
    log(f"  Found {total} results on arXiv")

    papers = []
    for entry in root.findall("a:entry", ns):
        title = entry.find("a:title", ns).text.strip().replace("\n", " ")
        summary = entry.find("a:summary", ns).text.strip().replace("\n", " ")
        published = entry.find("a:published", ns).text[:10]

        authors = []
        for author in entry.findall("a:author", ns):
            name = author.find("a:name", ns)
            if name is not None:
                authors.append(name.text)

        link = ""
        for link_el in entry.findall("a:link", ns):
            if link_el.get("rel") == "alternate" or link_el.get("title") == "pdf":
                link = link_el.get("href", "")
                break
        if not link:
            link_el = entry.find("a:link", ns)
            if link_el is not None:
                link = link_el.get("href", "")

        papers.append({
            "title": title,
            "authors": authors,
            "summary": summary[:2000],
            "link": link,
            "published": published,
            "source": "arXiv"
        })
    return papers

# ── PubMed fetcher (via NCBI E-utilities) ─────────────────────────────

def fetch_pubmed():
    """
    Fetch recent papers from PubMed via NCBI E-utilities.
    """
    log("Fetching PubMed papers...")

    # Step 1: Search
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + urlencode({
        "db": "pubmed",
        "term": PUBMED_QUERY,
        "retmax": str(MAX_PAPERS),
        "sort": "date",
        "retmode": "json",
        "datetype": "pdat",
        "mindate": "2026/01/01",
        "maxdate": "2026/12/31",
    })
    result = fetch_url(search_url)
    if not result:
        return []

    data = json.loads(result)
    ids = data.get("esearchresult", {}).get("idlist", [])
    if not ids:
        log("  No new papers found on PubMed")
        return []

    log(f"  Found {len(ids)} papers on PubMed")

    # Step 2: Fetch details
    fetch_url_e = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?" + urlencode({
        "db": "pubmed",
        "id": ",".join(ids),
        "retmode": "xml",
        "rettype": "abstract",
    })
    xml_text = fetch_url(fetch_url_e)
    if not xml_text:
        return []

    papers = []
    root = ElementTree.fromstring(xml_text)
    for article in root.findall(".//PubmedArticle"):
        title_el = article.find(".//ArticleTitle")
        title = "".join(title_el.itertext()) if title_el is not None else "No title"

        abstract_el = article.find(".//AbstractText")
        summary = "".join(abstract_el.itertext()) if abstract_el is not None else "No abstract"

        pmid = article.find(".//PMID")
        pmid_text = pmid.text if pmid is not None else ""

        authors = []
        for author in article.findall(".//Author"):
            last = author.find("LastName")
            fore = author.find("ForeName")
            if last is not None:
                name = f"{last.text}"
                if fore is not None:
                    name = f"{fore.text} {name}"
                authors.append(name)

        pub_date_el = article.find(".//PubDate")
        published = "".join(pub_date_el.itertext()) if pub_date_el is not None else ""

        papers.append({
            "title": title.strip(),
            "authors": authors,
            "summary": summary.strip()[:2000],
            "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid_text}/",
            "published": published.strip(),
            "source": "PubMed"
        })
    return papers

# ── LLM summarization ──────────────────────────────────────────────────

def summarize_with_llm(papers):
    """
    Send papers to DeepSeek/LLM for summarization.
    Returns the markdown digest string.
    """
    if not papers:
        return "No papers found today."

    # Build the prompt
    papers_text = ""
    for i, p in enumerate(papers, 1):
        papers_text += f"""
--- Paper {i} ---
Title: {p['title']}
Authors: {', '.join(p['authors'][:5])}{' et al.' if len(p['authors']) > 5 else ''}
Source: {p['source']}
Published: {p['published']}
Link: {p['link']}
Abstract: {p['summary']}
"""

    system_prompt = """You are a chemistry research assistant. Generate a daily literature digest in ENGLISH.

For each paper, provide:
1. **Title** (linked)
2. **Why this matters** — 1-2 sentences on significance
3. **Key contribution** — 2-3 sentences summarizing the main finding
4. **Relevance** — which area it relates to (organic synthesis, total synthesis, reaction mechanism, medicinal chemistry, DEL, catalysis, etc.)

Format in clean Markdown. Group related papers if possible. End with a "Quick Take" section — your overall assessment of what's most interesting today."""

    user_prompt = f"Here are today's papers from arXiv and PubMed. Generate a digest.\n\n{papers_text}"

    log(f"Sending {len(papers)} papers to LLM ({LLM_MODEL}) for summarization...")

    payload = json.dumps({
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 4096,
    }).encode("utf-8")

    resp = fetch_url(
        f"{LLM_BASE_URL.rstrip('/')}/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LLM_API_KEY}",
        },
    )
    if not resp:
        # Fallback: generate a simple digest without LLM
        return fallback_digest(papers)

    try:
        data = json.loads(resp)
        content = data["choices"][0]["message"]["content"]
        log("  LLM summarization complete")
        return content
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        log(f"  ⚠  LLM response parse error: {e}")
        return fallback_digest(papers)

def fallback_digest(papers):
    """Generate a simple digest without LLM (in case API call fails)."""
    lines = ["# Daily Literature Digest", f"**{datetime.now():%B %d, %Y}**\n"]
    for p in papers:
        lines.append(f"## {p['title']}")
        lines.append(f"**Authors:** {', '.join(p['authors'][:3])}")
        lines.append(f"**Source:** {p['source']} | **Published:** {p['published']}")
        lines.append(f"**Link:** {p['link']}")
        lines.append(f"\n{p['summary'][:500]}...\n")
    return "\n".join(lines)

# ── Email sending ────────────────────────────────────────────────────

def send_email(digest_md):
    """Send the digest via SMTP. Sends to yourself (SMTP_USER)."""
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

    # Plain text version
    msg.attach(MIMEText(digest_md, "plain", "utf-8"))

    # HTML version
    html = digest_md.replace("\n", "<br>\n")
    html_body = f"""<html><body style="font-family: -apple-system, sans-serif; max-width: 720px; margin: 0 auto;">
{html}
</body></html>"""
    msg.attach(MIMEText(html_body, "html", "utf-8"))

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
        # Print digest anyway so it shows in GitHub Actions logs
        print("\n=== DIGEST (email failed) ===")
        print(digest_md)

# ── Deduplication ──────────────────────────────────────────────────────

def deduplicate(papers):
    """Remove papers with very similar titles."""
    seen = set()
    unique = []
    for p in papers:
        key = p["title"].lower().strip()
        # Simple dedup: keep first 80 chars as key
        short_key = key[:80]
        if short_key not in seen:
            seen.add(short_key)
            unique.append(p)
    return unique

# ── Main ───────────────────────────────────────────────────────────────

def main():
    log("Starting daily literature digest...")

    if not LLM_API_KEY:
        log("⚠  LLM_API_KEY not set. Set up secrets before running.")
        sys.exit(1)

    # 1. Fetch papers from both sources
    arxiv_papers = fetch_arxiv()
    pubmed_papers = fetch_pubmed()

    all_papers = deduplicate(arxiv_papers + pubmed_papers)

    if not all_papers:
        log("No papers found from any source.")
        # Still send an email so you know it ran
        digest = "# Daily Literature Digest\n\nNo new papers found matching your criteria today."
        send_email(digest)
        return

    # Limit to MAX_PAPERS
    all_papers = all_papers[:MAX_PAPERS]
    log(f"Total unique papers to summarize: {len(all_papers)}")

    # 2. Summarize with LLM
    digest = summarize_with_llm(all_papers)

    # 3. Send email
    send_email(digest)

    # 4. Print to logs for visibility
    print(digest)

    log("✅ Done!")

if __name__ == "__main__":
    main()
