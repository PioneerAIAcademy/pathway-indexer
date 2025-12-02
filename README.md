# pathway-indexer

[![Release](https://img.shields.io/github/v/release/PioneerAIAcademy/pathway-indexer)](https://img.shields.io/github/v/release/PioneerAIAcademy/pathway-indexer)
[![Build status](https://img.shields.io/github/actions/workflow/status/PioneerAIAcademy/pathway-indexer/main.yml?branch=main)](https://github.com/PioneerAIAcademy/pathway-indexer/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/PioneerAIAcademy/pathway-indexer/branch/main/graph/badge.svg)](https://codecov.io/gh/PioneerAIAcademy/pathway-indexer)
[![Commit activity](https://img.shields.io/github/commit-activity/m/PioneerAIAcademy/pathway-indexer)](https://img.shields.io/github/commit-activity/m/PioneerAIAcademy/pathway-indexer)
[![License](https://img.shields.io/github/license/PioneerAIAcademy/pathway-indexer)](https://img.shields.io/github/license/PioneerAIAcademy/pathway-indexer)

Create and maintain the index for the BYU Pathway Missionary Assistant chatbot.

## 📖 Documentation

| Document                                   | Description                                      |
| ------------------------------------------ | ------------------------------------------------ |
| [Getting Started](docs/getting-started.md) | Installation, environment setup, and credentials |
| [Pipeline Guide](docs/pipeline-guide.md)   | Running the three main scripts                   |
| [Troubleshooting](docs/troubleshooting.md) | Common issues and solutions                      |

## What This Project Does

The **BYU Pathway Indexer** is a data pipeline that:

1. Crawls BYU Pathway websites (ACM, Missionary Services, Help Center, Student Services)
2. Downloads HTML and PDF content
3. Converts to markdown with metadata
4. Creates vector embeddings using OpenAI
5. Indexes to Pinecone for the [Missionary Chatbot](https://github.com/PioneerAIAcademy/pathway-chatbot)

## Quick Start

```bash
# Install dependencies
make install

# Run commands with Poetry
poetry run python main.py
poetry run python store.py
```

> **Note:** If you're using Poetry 2.x, the `poetry shell` command is not included by default.
> Use `poetry run` or `source .venv/bin/activate` instead.

See [Getting Started](docs/getting-started.md) for full setup instructions.

---

## Shared Data Directory

The `data` directory is excluded from git and managed via SSH to the production server.

### Setup

Contact @DallanQ to get:

1. SSH key file (`.pem`)
2. Your individual account credentials
3. Server connection details

### Usage

```bash
make pull-data   # Download data from shared server
make push-data   # Upload data to shared server
```

> **Important:**
> The shared data directory doesn't have version control. Add date-stamps to filenames so you don't accidentally overwrite files.

---

## Weekly: Load New Data

1. Create a new subdirectory in the `data/` folder (with today's date, e.g. `data_07_10_25/`)
2. Update your `.env` file with the new path: `DATA_PATH=data/data_07_10_25`

### Run Crawler

```bash
poetry run python main.py
```

### Load the Data into the Index

```bash
poetry run python store.py
```

> **Tip:**
> See [Pipeline Guide](docs/pipeline-guide.md) for detailed information on each script.

---

## Running the Langfuse Data Extraction

The Langfuse data extraction is run as a standalone script. This script will download and process data from Langfuse to extract user questions.

```bash
poetry run python extract_questions.py
```

By default, the script will process data from the last 7 days. You can change this by using the `--days` argument:

```bash
poetry run python extract_questions.py --days 14
```

---

## Related Projects

- [pathway-chatbot](https://github.com/PioneerAIAcademy/pathway-chatbot) - The RAG chatbot using this index
- [pathway-questions-topic-modelling](https://github.com/PioneerAIAcademy/pathway-questions-topic-modelling) - Topic analysis for user questions
