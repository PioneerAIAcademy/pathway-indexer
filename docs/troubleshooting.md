# Troubleshooting

## Common Errors

### Setup Issues

| Error                       | Solution                                                   |
| --------------------------- | ---------------------------------------------------------- |
| `python: command not found` | Install Python 3.12 or check PATH                          |
| `poetry: command not found` | `curl -sSL https://install.python-poetry.org \| python3 -` |
| `ModuleNotFoundError`       | Run `poetry install`, then activate venv                   |
| `API_KEY not found`         | Check `.env` file has all required keys                    |

### Crawling Errors

| Error                | Solution                                                    |
| -------------------- | ----------------------------------------------------------- |
| `403 Forbidden`      | Automatic Playwright fallback. Check if site requires auth. |
| `Connection timeout` | Auto-retry. Use production server for stability.            |

### Parsing Errors

| Error                   | Solution                                                 |
| ----------------------- | -------------------------------------------------------- |
| `LlamaParse rate limit` | It usually Auto-retries with backoff. Wait and continue. |
| `No markdown generated` | Check `pipeline_detailed_log.jsonl` for details          |
| Empty markdown files    | Check `error.csv`, verify LlamaParse API key             |

### Indexing Errors

| Error                      | Solution                                                 |
| -------------------------- | -------------------------------------------------------- |
| `No markdown files found`  | Run `main.py` first. Check `DATA_PATH` in `.env`         |
| `OpenAI rate limit`        | It usually Auto-retry (up to 25 times). Check API quota. |
| `Pinecone index not found` | Script creates it automatically on first run             |
| Files with 0 nodes         | Check if markdown has content beyond YAML header         |

## Investigating Issues

### Check Logs

```bash
# Find all errors
grep "FAILED" data/.../pipeline_detailed_log.jsonl

# Check specific URL
grep "your-url" data/.../pipeline_detailed_log.jsonl

# View error summary
cat data/.../error/error.csv
```

### Trace a URL

```bash
# 1. Find hash filename
grep "article/123" data/.../all_links.csv
# Output shows: ...,a3f5b9c2

# 2. Check downloaded file
ls data/.../crawl/html/a3f5b9c2.html

# 3. Check markdown output
cat data/.../out/from_html/a3f5b9c2.md

# 4. Check node count
grep "a3f5b9c2" data/.../node_counts_log.json
```

### Metrics Interpretation

After `main.py`:

```json
{
  "Files skipped": 320, // High = good (unchanged content)
  "Documents with errors": 2, // Should be low
  "MD files generated": 448 // Should match total documents
}
```

After `store.py`:

```json
{
  "Files with 0 nodes": 3, // Should be low
  "Total nodes": 6240, // Total searchable chunks
  "Average nodes per file": 14 // Typical: 10-20
}
```

## Quick Fixes

### Force Re-crawl

Delete timestamp file to re-crawl all content:

```bash
rm data/.../last_crawl_detail.json
poetry run python main.py
```

### Re-index Only

Skip crawling, just re-run indexing:

```bash
poetry run python store.py
```

### Clear and Start Fresh

```bash
rm -rf data/adata_old_folder/
# Update DATA_PATH to new folder
poetry run python main.py
poetry run python store.py
```

## Getting Help

1. Check logs first - they usually explain what went wrong
2. Review `error/error.csv` for failed items
3. Contact @DallanQ for access issues
