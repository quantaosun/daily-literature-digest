# CLAUDE.md — Daily Literature Digest

## Project Overview
A GitHub Actions workflow that searches PubMed for chemistry papers matching configured keywords, summarizes them via DeepSeek LLM, and emails a daily digest.

**Tracked topics:** organic synthesis, total synthesis, reaction mechanisms, medicinal chemistry, DEL, catalysis

## Key Files
- `digest.py` — Main script: PubMed search → LLM summarization → email sending
- `.github/workflows/daily-digest.yml` — GitHub Actions schedule (daily 9AM Beijing)
- `requirements.txt` — Only depends on `requests`

## Code Architecture

### `digest.py` flow:
1. `fetch_pubmed()` — NCBI E-utilities search + fetch
   - Searches last 60 days via `[PDAT]` date filter
   - No API key required for PubMed API
   - Uses `esearch.fcgi` → IDs → `esummary.fcgi` + `efetch.fcgi` for details
   - Returns list of dicts: `{title, journal, date, abstract, link, pmid}`
2. `summarize_with_llm()` — Sends papers to DeepSeek API
   - Falls back to `fallback_digest()` if LLM call fails
   - Prompt asks for: why matters, key contribution, relevance
3. `send_email()` — SMTP email via SSL (default port 465)

### Configuration (via GitHub Secrets)
| Env Var | Secret | Required |
|---------|--------|----------|
| `LLM_API_KEY` | `LLM_API_KEY` | Yes |
| `MAIL` | `MAIL` | Yes |
| `MAIL_PW` | `MAIL_PW` | Yes |
| `MAIL_SERVER` | `MAIL_SERVER` | No (default: smtp.qq.com) |
| `MAIL_PORT` | `MAIL_PORT` | No (default: 465) |
| `LLM_BASE_URL` | `LLM_BASE_URL` | No (default: https://api.deepseek.com) |
| `LLM_MODEL` | `LLM_MODEL` | No (default: deepseek-chat) |
| `MAX_PAPERS` | `MAX_PAPERS` | No (default: 8) |

## Customization

### Changing search keywords
Edit `KEYWORDS` list in `digest.py` (~line 47):
```python
KEYWORDS = ["keyword1", "keyword2", ...]
```
Keywords are combined with `OR` and searched in `[Title/Abstract]`.

### Changing search date range
Edit `timedelta(days=60)` in `fetch_pubmed()`.

## Dependencies
Only `requests` library (installed via pip in the workflow).

## Conventions
- English-only output (digest and email)
- LLM model: DeepSeek Chat (or any OpenAI-compatible API)
- All SMTP config via env vars, never hardcoded
- Papers limited by `MAX_PAPERS` after fetching all matching IDs
