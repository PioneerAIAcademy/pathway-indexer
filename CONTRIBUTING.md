# Contributing to `pathway-indexer`

Contributions are welcome, and they are greatly appreciated! Every little bit helps, and credit will always be given.

## Ways to Contribute

### Report Bugs

Report bugs at https://github.com/PioneerAIAcademy/pathway-indexer/issues

If you are reporting a bug, please include:

- Your operating system name and version
- Any details about your local setup that might be helpful in troubleshooting
- Detailed steps to reproduce the bug

### Fix Bugs or Implement Features

Look through the GitHub issues for bugs or features:

- Issues tagged with "bug" and "help wanted" are open for fixes
- Issues tagged with "enhancement" and "help wanted" are open for implementation

### Improve Documentation

Documentation improvements are always welcome! You can contribute by:

- Updating the docs in the [`docs/`](docs/) folder
- Improving docstrings in the code
- Writing blog posts or tutorials

### Submit Feedback

The best way to send feedback is to file an issue at https://github.com/PioneerAIAcademy/pathway-indexer/issues.

If you are proposing a new feature:

- Explain in detail how it would work
- Keep the scope as narrow as possible, to make it easier to implement
- Remember that this is a volunteer-driven project, and that contributions are welcome!

## Getting Started with Development

Ready to contribute? Here's how to set up `pathway-indexer` for local development.

### Prerequisites

- Python 3.12
- Poetry
- Git

For detailed setup instructions, see [Getting Started](docs/getting-started.md).

### Setup Steps

1. Fork the `pathway-indexer` repo on GitHub

2. Clone your fork locally:

   ```bash
   git clone git@github.com:YOUR_NAME/pathway-indexer.git
   cd pathway-indexer
   ```

3. Install the environment:

   ```bash
   make install
   ```

   This will:

   - Install dependencies via Poetry
   - Set up pre-commit hooks for code quality

4. Create a branch for your changes:

   ```bash
   git checkout -b name-of-your-bugfix-or-feature
   ```

5. Make your changes locally

6. Add test cases for your functionality to the `tests/` directory

7. Run code quality checks:

   ```bash
   make check    # Run linters and type checking
   make test     # Run tests with coverage
   ```

8. Commit and push your changes:

   ```bash
   git add .
   git commit -m "Your detailed description of your changes"
   git push origin name-of-your-bugfix-or-feature
   ```

9. Submit a pull request through the GitHub website

## Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1. **Include tests**: The pull request should include tests for new functionality
2. **Update documentation**: If the PR adds functionality, update the docs
3. **Pass checks**: Ensure `make check` and `make test` pass
4. **Follow conventions**: Follow the existing code style and naming conventions

## Development Resources

- [Getting Started](docs/getting-started.md) - Setup and installation
- [Pipeline Guide](docs/pipeline-guide.md) - Understanding the scripts
- [Project Structure](docs/project-structure.md) - Codebase layout
- [Troubleshooting](docs/troubleshooting.md) - Common issues

## Questions?

If you have questions or need help, feel free to:

- Open an issue on GitHub
- Check the [docs](docs/) folder for documentation
- Contact the project maintainers

Thank you for contributing! 🙏
