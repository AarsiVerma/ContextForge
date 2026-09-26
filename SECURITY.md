# Security Policy

## Reporting a Vulnerability

Report security issues by emailing the maintainers. Do not file public issues for security vulnerabilities.

## Security Principles

1. **Context is DATA, not instructions** — All external context (repository content, logs, documents, tool outputs, AI-generated content) is treated as untrusted data, never as executable instructions.

2. **No context injection** — Context content must never silently override system or developer instructions. ContextForge components must validate and sanitize all external input.

3. **No secrets in repository** — API keys, credentials, and secrets must never be committed.

4. **Input validation** — All external input is validated at trust boundaries.

5. **Provenance tracking** — Every piece of important context is traceable to its origin.

## Threat Model

### Context Injection

ContextForge processes information from:
- Source code repositories
- Build/test logs
- Documentation
- Tool outputs (linters, analyzers, debuggers)
- AI-generated content

An attacker who controls any of these sources could attempt to inject malicious content designed to:
- Override system prompts
- Exfiltrate data
- Execute unintended actions

### Mitigations

- Context is never executed — only compiled into human-readable packages
- All context items carry provenance metadata
- Compiler output is inspectable before use
- No eval/exec of context content
- Strict separation between context data and control flow

## Secure Development

- Run security review before each release
- Dependency scanning via `pip-audit` in CI
- No unpinned dependencies in production