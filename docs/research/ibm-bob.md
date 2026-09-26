# IBM Bob 2.0 Research

## Source
- Official website: https://www.ibm.com/products/bob
- Documentation: https://www.ibm.com/products/bob/docs (requires JavaScript)
- Marketing pages and testimonials as of Sep 2026

## Core Capabilities

### Modes
1. **Agent Mode** - For implementation and debugging tasks. Bob can spawn focused agents and subagents.
2. **Plan Mode** - For planning and investigation planning.
3. **Ask Mode** - For questions and understanding code.

### Subagents
- "I can spawn focused agents and subagents that contribute to your code base."
- "Each agent uses its own context, tools, and skills"
- "Run work in parallel to handle long-running tasks in the background"
- "Return only what matters" - isolated contexts, clean summaries

### Bob Shell
- CLI integration for interactive work
- Script repetitive tasks
- Embed into CI/CD pipelines
- "Bring agents to your command line"

### MCP (Model Context Protocol)
- "3 prompts. That's all it took to build a production-ready MCP server."
- Bob can build and consume MCP servers

### Bob Shell (CLI)
- Interactive work
- Script repetitive tasks
- Embed into CI/CD pipelines
- "Bring agents to your command line"

### Guardrails
- "Operates in different modes, allowing you to approve its suggestions before any changes are made to your source code"
- "If you ask it about a non-existent RPG op-code, it won't 'hallucinate' an answer; it will simply state that it doesn't understand"
- Controlled, predictable behavior for enterprise development

### Literate Coding
- Natural language to code generation
- Forget context-switching between chat windows and editor

## Integration Mechanisms (Documented)

### MCP (Model Context Protocol)
- Bob can build MCP servers
- Bob can consume MCP servers
- This is the primary documented extension mechanism

### Bob Shell (CLI)
- Interactive use
- Scripting
- CI/CD integration

### IDE Integration
- VS Code extension (implied)
- IDE integration mentioned

### Enterprise Integrations
- Red Hat
- Instana
- IBM ecosystem

## What's NOT Documented (or unclear)

1. **Direct API for context injection** - No documented REST/gRPC API for external context management
2. **Programmatic subagent control** - Subagents appear to be Bob-internal
3. **Context package format** - No documented standard format for feeding context to Bob
4. **MCP server details** - Can Bob act as MCP client? Can it consume external context via MCP?
5. **Headless/automated mode** - Unclear if Bob can run fully headless for hackathon demo
6. **Programmatic session control** - No documented API for controlling Bob sessions programmatically

## Hackathon Integration Strategy

### Recommended Approach (Based on Documented Capabilities)

Since there's no documented public API for direct context injection, the most reliable integration for a hackathon demo is:

1. **MCP Integration** - Build a ContextForge MCP server that Bob can query for context
   - Bob can consume MCP servers (documented: "3 prompts to build MCP server")
   - ContextForge exposes context via MCP resources/tools

2. **Bob Shell (CLI) Workflow** - Use Bob Shell for scripted interaction
   - ContextForge CLI generates context package
   - Bob Shell reads the package file
   - Human-in-the-loop for approval (guardrails)

3. **File-based Context Handoff** - Simple, reliable fallback
   - ContextForge writes context package to file
   - Bob reads file via its file reading capabilities
   - Most reliable for hackathon demo

### Recommended Demo Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Bug       │────▶│  Bob Plan    │────▶│ Investigation   │
│   Report    │     │  Mode        │     │ Plan            │
└─────────────┘     └──────────────┘     └────────┬────────┘
                                                   │
                                                   ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Context    │◀───▶│  Bob Agent   │◀───▶│ Subagents for   │
│  Package    │     │  Mode        │     │ Parallel Invest │
└─────────────┘     └──────────────┘     └─────────────────┘
       ▲
       │
┌──────┴──────┐
│ ContextForge │
│  Pipeline   │
└─────────────┘
```

### MCP Server Approach (If Feasible)
- ContextForge runs as MCP server
- Bob queries ContextForge for context via MCP
- ContextForge provides: context items, search, ranking, selection

### Fallback: File-Based Handoff
- ContextForge CLI: `contextforge pipeline ... --output package.md`
- Bob reads `package.md` via file operations
- Most reliable for hackathon demo

## Key Bob Capabilities for Demo

1. **Parallel Subagents** - Each investigation stream gets isolated context
2. **Plan Mode** - Create investigation plan
3. **Agent Mode** - Execute investigation and implement fix
4. **Guardrails** - Human approval before code changes
5. **Bob Shell** - CLI for automation
6. **MCP** - Potential integration point

## Limitations for Hackathon

1. No programmatic API for context injection
2. Subagents are Bob-internal, not programmatically controllable
3. Context window management is Bob-internal
4. No webhook/event system for ContextForge to push context
5. Must work with Bob's existing UI/CLI workflow

## Demo Strategy

**Primary**: File-based context handoff via ContextForge CLI
- ContextForge generates `debugging_context.md`
- Bob reads file during investigation
- Reliable, demonstrable, no API dependencies

**Secondary (if time permits)**: MCP server
- ContextForge exposes MCP resources
- Bob queries via MCP
- More impressive but riskier

## Next Steps

1. Create hackathon.md with demo plan
2. Build demo application with 5 reproducible bugs
3. Implement ContextForge MCP server (optional)
4. Create demo scripts for file-based workflow
5. Design 5 debugging scenarios
6. Run baseline vs ContextForge experiments