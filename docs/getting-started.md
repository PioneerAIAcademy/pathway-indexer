# Getting Started

## Prerequisites

- **Python 3.12** (specifically 3.12.x)
- **Poetry** (package manager)
- **API Keys** for: LlamaParse, OpenAI, Pinecone, Langfuse

## Installation

```bash
git clone <repository-url>
cd pathway-indexer
make install
```

Activate the environment:

```bash
source .venv/bin/activate
# Or use: poetry run <command>
```

## Environment Setup

Copy and configure your `.env` file:

```bash
cp .env.example .env
```

**Note:** Change `DATA_PATH` each time you run the pipeline to avoid overwriting previous data.

## Development vs Production

### Local Development

- For testing and debugging
- Request OpenAI key from @DallanQ
- Get your own free accounts for Pinecone, LlamaParse, Langfuse

### Production Server (Dallan's Machine)

- For weekly crawls
- Much faster, stable network
- All API keys already configured
- SSH access: Contact @DallanQ for credentials

## First Run

1. Update `DATA_PATH` in `.env` to a new folder name
2. Run main pipeline (usually takes 2-3 hours):
   ```bash
   poetry run python main.py
   ```
3. Run vector indexer (5-15 minutes):
   ```bash
   poetry run python store.py
   ```

## Quick Troubleshooting

| Error                       | Solution                                   |
| --------------------------- | ------------------------------------------ |
| `python: command not found` | Activate venv: `source .venv/bin/activate` |
| `ModuleNotFoundError`       | Run `poetry install`                       |
| `API_KEY not found`         | Check your `.env` file                     |
