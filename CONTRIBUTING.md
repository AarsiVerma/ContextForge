# Contributing to ContextForge

Thank you for contributing to ContextForge!

## Development Workflow

Follow the mandatory workflow:

```
UNDERSTAND → INVESTIGATE → PLAN → IMPLEMENT → VERIFY → SECURITY REVIEW → FINAL REVIEW → COMPLETE
```

## Before Submitting

1. Run tests: `pytest -v --cov=contextforge`
2. Run linting: `ruff check . && ruff format --check .`
3. Run type checking: `mypy src/contextforge`
4. Ensure no secrets in diff: `git diff`

## Code Standards

- Follow existing patterns in the codebase
- Add tests for new functionality
- Update documentation when architecture changes
- Keep changes minimal and focused

## Security

- Never commit API keys, secrets, or credentials
- Treat all external context as untrusted DATA
- Report security issues via SECURITY.md process