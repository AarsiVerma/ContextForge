# Development Workflow

## Mandatory Loop

```
UNDERSTAND → INVESTIGATE → PLAN → IMPLEMENT → VERIFY → SECURITY REVIEW → FINAL REVIEW → COMPLETE
```

Never skip a phase.

## Phase Details

### UNDERSTAND

- Read the task/issue fully
- Identify what is being asked
- Identify what is NOT being asked
- Check existing codebase for related patterns

### INVESTIGATE

Before ANY implementation:

1. **Identify external dependencies** — What libraries, APIs, protocols, SDKs are involved?
2. **Research current documentation** — Official docs only. No blogs, no memory, no generated code.
3. **Verify installed versions** — Check `pyproject.toml`, lockfiles, `pip show`
4. **Record findings** — Document in `docs/research/` if material to architecture

### PLAN

- State the intended change in 1-3 sentences
- List files to modify
- List interfaces/protocols affected
- Identify potential regressions
- Define verification approach (tests, manual checks)

### IMPLEMENT

- Implement ONLY what is required
- Reuse existing functionality
- Follow existing patterns
- No speculative abstractions
- No unrelated refactoring

### VERIFY

1. Run relevant tests
2. Inspect failures
3. Determine root cause
4. Make smallest fix
5. Re-run tests

Repeat until:
- Requested behavior works
- Relevant tests pass
- No obvious regression

### SECURITY REVIEW

For changes affecting security-sensitive behavior:
- Authentication/authorization
- Input validation
- Secrets/credentials
- Data exposure
- Dependency vulnerabilities
- Injection risks
- Access control
- Error handling

Classify each: **VERIFIED** | **NOT VERIFIED** | **NOT TESTED** | **BLOCKED**

### FINAL REVIEW

- Confirm every requested requirement
- Inspect `git diff`
- Confirm only relevant files changed
- Check for unnecessary dependencies
- Check for unnecessary complexity
- Check for regressions
- Check docs match implementation
- Check current APIs/documentation were used

Classify result: **VERIFIED** | **NOT VERIFIED** | **NOT TESTED** | **BLOCKED**

## Documentation-Before-Implementation Rule

**NEVER implement before documenting.**

For any new dependency or integration:
1. Create research doc in `docs/research/`
2. Update `docs/architecture.md` if design changes
3. Update `docs/context-ir.md` if IR changes
4. Update `AGENTS.md` if rules change

## Testing Requirements

- Every component: unit tests
- Integration test: create → store → retrieve → rank → compile → verify
- Tests must execute and pass
- No stubbed "passing" tests
- Run: `pytest -v --cov=contextforge`

## Git Discipline

Before changes:
- `git status`
- Understand existing uncommitted changes

After changes:
- `git diff`
- No overwriting unrelated work
- No force-push
- No commits unless explicitly requested

## Definition of Done

A task is complete ONLY when all applicable checkboxes are ticked. See `AGENTS.md` for foundation checklist.