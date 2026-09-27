"""Command-line interface for ContextForge."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from contextforge import (
    ContextIR,
    ContextSelector,
    ContextType,
    DeterministicRanker,
    FileSource,
    LocalRetriever,
    SimpleCompiler,
    SQLiteStore,
    TaskSource,
    TestResultSource,
    TextSource,
    ToolOutputSource,
)
from contextforge.inspection import DebugContext


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="contextforge",
        description="ContextForge - Model-agnostic context management for AI coding agents",
    )
    parser.add_argument(
        "--db",
        default="contextforge.db",
        help="Path to SQLite database",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest context from sources")
    ingest_parser.add_argument("--path", required=True, help="Path to source files")
    ingest_parser.add_argument("--task-id", required=True, help="Task ID")
    ingest_parser.add_argument("--patterns", nargs="+", default=["*.py", "*.md", "*.txt"])
    ingest_parser.add_argument("--output", help="Output file for items (JSON)")

    # Retrieve command
    retrieve_parser = subparsers.add_parser("retrieve", help="Retrieve relevant context")
    retrieve_parser.add_argument("--task-id", required=True, help="Task ID")
    retrieve_parser.add_argument("--query", help="Search query")
    retrieve_parser.add_argument("--types", nargs="+", help="Context types to retrieve")
    retrieve_parser.add_argument("--limit", type=int, default=50, help="Max items to retrieve")

    # Rank command
    rank_parser = subparsers.add_parser("rank", help="Rank context items")
    rank_parser.add_argument("--task-id", required=True, help="Task ID")
    rank_parser.add_argument("--query", help="Search query")
    rank_parser.add_argument("--limit", type=int, default=50)

    # Compile command
    compile_parser = subparsers.add_parser("compile", help="Compile context package")
    compile_parser.add_argument("--task-id", required=True, help="Task ID")
    compile_parser.add_argument("--query", help="Search query")
    compile_parser.add_argument("--limit", type=int, default=50)
    compile_parser.add_argument("--output", help="Output file for package")
    compile_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")



    # Pipeline command (end-to-end)
    pipeline_parser = subparsers.add_parser("pipeline", help="Run full pipeline")
    pipeline_parser.add_argument("--path", required=True, help="Path to source files")
    pipeline_parser.add_argument("--task-id", required=True, help="Task ID")
    pipeline_parser.add_argument("--task-desc", required=True, help="Task description")
    pipeline_parser.add_argument("--query", help="Search query")
    pipeline_parser.add_argument("--output", help="Output file for package")
    pipeline_parser.add_argument("--patterns", nargs="+", default=["*.py", "*.md", "*.txt"])
    pipeline_parser.add_argument("--limit", type=int, default=50, help="Max items to retrieve")

    return parser


def cmd_ingest(args: argparse.Namespace) -> int:
    """Ingest context from file sources."""
    store = SQLiteStore(Path(args.db))
    store.initialize()

    source = FileSource(
        root_path=Path(args.path),
        patterns=args.patterns,
        task_id=args.task_id,
    )
    items = source.fetch()

    for item in items:
        store.put_item(item)

    if args.output:
        with open(args.output, "w") as f:
            json.dump([item.model_dump(mode="json") for item in items], f, indent=2)

    print(f"Ingested {len(items)} items from {args.path}")
    return 0


def cmd_retrieve(args: argparse.Namespace) -> int:
    """Retrieve relevant context."""
    store = SQLiteStore(Path(args.db))
    store.initialize()

    retriever = LocalRetriever(store)
    items = retriever.retrieve(
        task_id=args.task_id,
        query=args.query,
        types=args.types,
        limit=args.limit,
    )

    for item in items:
        print(f"[{item.type.value}] {item.source}: {item.content[:100]}...")

    return 0


def cmd_rank(args: argparse.Namespace) -> int:
    """Rank context items."""
    store = SQLiteStore(Path(args.db))
    store.initialize()

    retriever = LocalRetriever(store)
    items = retriever.retrieve(task_id=args.task_id, limit=args.limit)

    ranker = DeterministicRanker()
    ranked = ranker.rank(items, args.task_id, args.query)

    for i, item in enumerate(ranked):
        print(f"{i+1}. [{item.type.value}] {item.source} (score: {item.importance:.2f}): {item.content[:80]}...")

    return 0


def cmd_compile(args: argparse.Namespace) -> int:
    """Compile context package."""
    store = SQLiteStore(Path(args.db))
    store.initialize()

    ir = store.get_ir_by_task(args.task_id)
    if not ir:
        print(f"No ContextIR found for task {args.task_id}")
        return 1

    retriever = LocalRetriever(store)
    items = retriever.retrieve(task_id=args.task_id, query=args.query, limit=args.limit)

    ranker = DeterministicRanker()
    ranked = ranker.rank(items, args.task_id, args.query)

    compiler = SimpleCompiler()
    package = compiler.compile(ir, ranked, query=args.query)

    if args.output:
        if args.format == "markdown":
            with open(args.output, "w") as f:
                f.write(package.to_markdown())
        else:
            with open(args.output, "w") as f:
                f.write(package.to_json())
    else:
        if args.format == "markdown":
            print(package.to_markdown())
        else:
            print(package.to_json())

    return 0


def cmd_pipeline(args: argparse.Namespace) -> int:
    """Run the full pipeline."""
    store = SQLiteStore(Path(args.db))
    store.initialize()

    # Create inspector
    debug_ctx = DebugContext(args.task_id, args.task_desc)

    # 1. Ingest from multiple sources
    all_items = []

    # Task source
    task_source = TaskSource(
        task_description=args.task_desc,
        task_id=args.task_id,
    )
    task_items = task_source.fetch()
    all_items.extend(task_items)
    debug_ctx.raw_sources.append(task_source)

    # File source
    file_source = FileSource(
        root_path=Path(args.path),
        patterns=args.patterns,
        task_id=args.task_id,
    )
    file_items = file_source.fetch()
    all_items.extend(file_items)
    debug_ctx.raw_sources.append(file_source)

    # Log source (if logs directory exists)
    logs_path = Path(args.path).parent / "logs"
    if logs_path.exists():
        for log_file in logs_path.glob("*.log"):
            log_source = TextSource(
                content=log_file.read_text(),
                source_id=str(log_file.relative_to(Path(args.path).parent)),
                context_type=ContextType.LOG,
                task_id=args.task_id,
                importance=0.7,
            )
            log_items = log_source.fetch()
            all_items.extend(log_items)
            debug_ctx.raw_sources.append(log_source)

    # Test results source - use TestResultSource
    test_result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        cwd=Path(args.path).parent,
        capture_output=True,
        text=True,
        timeout=60,
    )
    test_source = TestResultSource(
        test_output=test_result.stdout + test_result.stderr,
        test_file="demo-app/tests/",
        task_id=args.task_id,
        observer="pytest",
        importance=0.8,
    )
    test_items = test_source.fetch()
    all_items.extend(test_items)
    debug_ctx.raw_sources.append(test_source)

    # Tool output source - capture any tool output (linter, etc.)
    tool_source = ToolOutputSource(
        tool_name="pytest",
        output=test_result.stdout + test_result.stderr,
        task_id=args.task_id,
        observer="tool_ingestion",
        importance=0.7,
    )
    tool_items = tool_source.fetch()
    all_items.extend(tool_items)
    debug_ctx.raw_sources.append(tool_source)

    raw_items = all_items
    debug_ctx.raw_sources = debug_ctx.raw_sources
    debug_ctx.normalized_items = raw_items

    # Record ingestion for each source
    for source in debug_ctx.raw_sources:
        items = source.fetch()
        debug_ctx.inspector.record_ingestion(items)

    # 2. Store items
    for item in raw_items:
        store.put_item(item)

    # 3. Create IR
    ir = ContextIR(task_id=args.task_id, task_description=args.task_desc)
    for item in raw_items:
        ir.add_item(item)
    store.put_ir(ir)

    # 4. Retrieve
    retriever = LocalRetriever(store)
    candidates = store.list_items(task_id=args.task_id, limit=args.limit)
    retrieved = retriever.retrieve(task_id=args.task_id, query=args.query, limit=args.limit)
    debug_ctx.candidates = candidates
    debug_ctx.retrieved_items = retrieved
    debug_ctx.inspector.record_retrieval(args.query, candidates, retrieved)

    # 5. Rank
    ranker = DeterministicRanker()
    ranked = ranker.rank(retrieved, args.task_id, args.query)
    debug_ctx.ranked_items = ranked
    debug_ctx.inspector.record_ranking(retrieved, ranked)

    # 6. Select
    selector = ContextSelector()
    selection = selector.select(ranked, args.task_id, args.query)
    debug_ctx.selection_result = selection
    debug_ctx.inspector.record_selection(selection)

    # 7. Compile
    compiler = SimpleCompiler()
    # Create debugging state with rejected hypotheses
    from contextforge.models.debugging_state import (
        DebuggingState,
        DebuggingStatus,
        RejectedHypothesis,
    )
    debugging_state = DebuggingState(
        task_id=args.task_id,
        task_description=args.task_desc,
        status=DebuggingStatus.ACTIVE
    )
    # Add some example rejected hypotheses for demo
    debugging_state.add_rejected_hypothesis(RejectedHypothesis(
        hypothesis="JWT secret mismatch",
        investigation="Checked JWT_SECRET config",
        result="FALSE",
        evidence=[],
        rejected_by="debugger"
    ))
    debugging_state.add_rejected_hypothesis(RejectedHypothesis(
        hypothesis="Refresh token rotation race condition",
        investigation="Analyzed token refresh flow",
        result="INCONCLUSIVE",
        evidence=[],
        rejected_by="debugger"
    ))
    package = compiler.compile_with_selection(ir, ranked, selection, query=args.query, debugging_state=debugging_state)
    debug_ctx.final_package = package
    debug_ctx.inspector.record_compilation(package, selection)

    # Output
    if args.output:
        with open(args.output, "w") as f:
            f.write(package.to_markdown())
    else:
        print(package.to_markdown())

    # Print inspection summary
    if args.verbose:
        debug_ctx.inspector.print_summary()

    print(f"\nPipeline complete: {selection.metrics['selected_items']} items selected, "
          f"{package.total_tokens} tokens")

    return 0


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        "ingest": cmd_ingest,
        "retrieve": cmd_retrieve,
        "rank": cmd_rank,
        "compile": cmd_compile,
        "pipeline": cmd_pipeline,
    }

    if args.command not in commands:
        parser.print_help()
        return 1

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())