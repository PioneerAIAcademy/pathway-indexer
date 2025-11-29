# pathway-indexer

[![Release](https://img.shields.io/github/v/release/PioneerAIAcademy/pathway-indexer)](https://img.shields.io/github/v/release/PioneerAIAcademy/pathway-indexer)
[![Build status](https://img.shields.io/github/actions/workflow/status/PioneerAIAcademy/pathway-indexer/main.yml?branch=main)](https://github.com/PioneerAIAcademy/pathway-indexer/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/PioneerAIAcademy/pathway-indexer/branch/main/graph/badge.svg)](https://codecov.io/gh/PioneerAIAcademy/pathway-indexer)
[![Commit activity](https://img.shields.io/github/commit-activity/m/PioneerAIAcademy/pathway-indexer)](https://img.shields.io/github/commit-activity/m/PioneerAIAcademy/pathway-indexer)
[![License](https://img.shields.io/github/license/PioneerAIAcademy/pathway-indexer)](https://img.shields.io/github/license/PioneerAIAcademy/pathway-indexer)

Data pipeline that powers the [BYU Pathway Missionary-Assistant Chatbot](https://missionary-chat.onrender.com/).

This pipeline automatically crawls BYU Pathway websites, downloads content, converts to markdown, creates vector embeddings, and indexes to Pinecone for semantic search.

## Documentation

📚 **[Complete Documentation on Wiki →](https://github.com/PioneerAIAcademy/pathway-indexer/wiki)**

- [Getting Started](https://github.com/PioneerAIAcademy/pathway-indexer/wiki/Getting-Started) - Installation and setup
- [Pipeline Overview](https://github.com/PioneerAIAcademy/pathway-indexer/wiki/Pipeline-Overview) - Understanding the three main scripts
- [Main Pipeline](https://github.com/PioneerAIAcademy/pathway-indexer/wiki/Main-Pipeline) - Running `main.py`
- [Vector Indexing](https://github.com/PioneerAIAcademy/pathway-indexer/wiki/Vector-Indexing) - Running `store.py`
- [Common Tasks](https://github.com/PioneerAIAcademy/pathway-indexer/wiki/Common-Tasks) - Troubleshooting and how-tos

## Quick Start

Install dependencies and pre-commit hooks:

```bash
make install
```

Activate the virtual environment:

```bash
source .venv/bin/activate
# Or use: poetry run <command>
```

For detailed setup instructions, environment configuration, and first run guide, see the **[Getting Started Guide](https://github.com/PioneerAIAcademy/pathway-indexer/wiki/Getting-Started)** on the wiki.

## Running the Pipeline

See the wiki for detailed guides:

- **[Main Pipeline Guide](https://github.com/PioneerAIAcademy/pathway-indexer/wiki/Main-Pipeline)** - Crawling and parsing (`main.py`)
- **[Vector Indexing Guide](https://github.com/PioneerAIAcademy/pathway-indexer/wiki/Vector-Indexing)** - Embedding and indexing (`store.py`)
- **[User Feedback Guide](https://github.com/PioneerAIAcademy/pathway-indexer/wiki/User-Feedback-Pipeline)** - Extracting questions (`extract_questions.py`)

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Related Projects

- **Chatbot**: [pathway-chatbot](https://github.com/DallanQ/pathway-chatbot) - The RAG chatbot that uses this index
- **Live Demo**: [missionary-chat.onrender.com](https://missionary-chat.onrender.com/)

## License

This project is licensed under the terms in the [LICENSE](LICENSE) file.
