# Pipeline Guide

## Overview

```
Websites → main.py → Markdown files → store.py → Pinecone → Chatbot
```

## main.py - Data Collection

**Purpose:** Crawl websites, download content, convert to markdown

**Duration:** 2-3 hours

### What It Does

1. **Get Indexes**: Crawls 4 index pages to collect all URLs

   - ACM Site (CSS selectors)
   - Missionary Services (scrape navigation)
   - Help Center (API with pagination)
   - Student Services (Playwright for JavaScript)

2. **Crawl Data**: Downloads HTML/PDF files

   - Uses content hashing to detect changes
   - Skips unchanged files (saves time)
   - Retries failed requests with Playwright fallback

3. **Parse Files**: Converts to markdown
   - Cleans HTML (removes navigation, scripts)
   - Sends to LlamaParse for markdown conversion
   - Adds YAML frontmatter with metadata

### Output

```
data/DATA_PATH/
├── all_links.csv                # All URLs collected
├── crawl/html/*.html            # Downloaded HTML
├── crawl/pdf/*.pdf              # Downloaded PDFs
├── out/from_html/*.md           # Markdown from HTML
├── out/from_pdf/*.md            # Markdown from PDF
├── error/error.csv              # Failed URLs
├── pipeline_detailed_log.jsonl  # Processing log
└── last_crawl_detail.json       # Timestamps
```

---

## store.py - Vector Indexing

**Purpose:** Create embeddings from markdown, index to Pinecone

**Duration:** 5-15 minutes

**Prerequisites:** main.py must complete first

### What It Does

1. **Load Documents**: Reads markdown files from `out/`
2. **Parse Nodes**: Splits documents into paragraphs using AltNodeParser
   - Adds context windows (surrounding paragraphs)
   - Propagates headers and metadata
3. **Generate Embeddings**: OpenAI `text-embedding-3-large` (3072 dimensions)
4. **Index to Pinecone**: Uploads vectors with metadata

### Output

- Vectors in Pinecone database (searchable by chatbot)
- `node_counts_log.json` - Nodes per file
- Files with 0 nodes logged in `error/error.csv`

---

## extract_questions.py - User Feedback

**Purpose:** Download user questions from Langfuse for analysis

**Duration:** 1-10 minutes

**When to Run:** Optional, independent of other scripts

### Usage

```bash
# Last 7 days (default)
poetry run python extract_questions.py

# Last 30 days
poetry run python extract_questions.py --days 30
```

### Output

```
data/DATA_PATH/langfuse/
├── traces_YYYY-MM-DD.csv                 # Complete trace data
├── observations_YYYY-MM-DD.csv           # Individual steps
└── extracted_user_inputs_YYYY-MM-DD.csv  # Cleaned questions
```

---

## Typical Weekly Workflow

```bash
# 1. SSH to production (or run locally for testing)
ssh your_username@dallan-server

# 2. Navigate to project
cd /path/to/pathway-indexer

# 3. Update DATA_PATH in .env to new folder e.g.
# DATA_PATH=data/adata_12_02_25/

# 4. Run main pipeline
poetry run python main.py

# 5. Run vector indexer
poetry run python store.py

# 6. Optional: Extract feedback
poetry run python extract_questions.py --days 7
```

> **IMPORTANT:** After each crawl, check `metrics_explanation.log` and `error/error.csv` and compare with previous crawls to ensure expected files are processed and no links are missing.
