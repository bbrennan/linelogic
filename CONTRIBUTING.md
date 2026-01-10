# Contributing to LineLogic

Thank you for your interest in contributing to LineLogic! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and professional
- Focus on constructive feedback
- Help maintain a welcoming environment

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/linelogic.git`
3. Set up the development environment: `make setup`
4. Create a feature branch: `git checkout -b feature/your-feature-name`

## Development Workflow

### Setting Up Your Environment

```bash
make setup
source .venv/bin/activate
```

### Before Committing

```bash
make format      # Format code
make lint        # Check linting
make type-check  # Run type checking
make test        # Run tests
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
pytest tests/test_odds.py

# Run specific test
pytest tests/test_odds.py::test_american_to_implied_prob
```

## Contribution Guidelines

### Code Style

- We use **ruff** for formatting and linting
- We use **mypy** for type checking
- Follow PEP 8 conventions
- Type hints are required for all functions
- Write docstrings for all public functions and classes

### Commit Messages

Use conventional commit format:

```
feat: add Kelly criterion calculator
fix: correct vig removal for edge case
docs: update data sources documentation
test: add tests for rate limiter
refactor: simplify cache key generation
```

### Pull Requests

1. Ensure all tests pass
2. Add tests for new functionality
3. Update documentation as needed
4. Keep PRs focused on a single concern
5. Reference any related issues

### Testing Requirements

- Unit tests for all new functions
- Integration tests for provider implementations
- Aim for >80% code coverage
- Include edge cases and error scenarios

### Documentation

- Update relevant docs in `docs/` folder
- Add docstrings to all public APIs
- Update README.md if needed
- Create ADR for architectural decisions

## Areas for Contribution

### High Priority
- Additional sport adapters (NFL, MLB, MMA)
- Alternative odds providers
- Improved feature engineering
- Backtesting framework enhancements

### Medium Priority
- UI/UX improvements
- Additional evaluation metrics
- Performance optimizations
- Documentation improvements

### Low Priority
- Code cleanup and refactoring
- Additional unit tests
- Example notebooks

## Reporting Bugs

Use GitHub Issues with:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version)
- Relevant logs or error messages

## Suggesting Features

Use GitHub Issues with:
- Clear description of the feature
- Use case and motivation
- Proposed implementation approach
- Any alternatives considered

## Questions?

- Check existing documentation in `docs/`
- Search existing GitHub Issues
- Open a new issue with the "question" label

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
