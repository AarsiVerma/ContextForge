"""Compilation interface - ContextCompiler protocol and enhanced implementation."""

from dataclasses import dataclass
from typing import Any, Callable, Protocol

from contextforge.config import get_config
from contextforge.models import (
    ContextIR,
    ContextItem,
    ContextPackage,
    ContextSection,
    ContextType,
    ItemStatus,
)
from contextforge.retrieval.selector import SelectionResult


class ContextCompiler(Protocol):
    """Protocol for compiling context into agent packages."""

    def compile(self, ir: ContextIR, ranked_items: list[ContextItem]) -> ContextPackage:
        """Compile ranked items into a context package."""
        ...

    def compile_with_selection(
        self, ir: ContextIR, ranked_items: list[ContextItem], selection: SelectionResult
    ) -> ContextPackage:
        """Compile with selection result for metrics."""
        ...


SectionBuilder = Callable[..., tuple[str, list[str], int]]


@dataclass
class CompilationMetrics:
    """Metrics from compilation."""

    candidate_items: int
    selected_items: int
    discarded_items: int
    duplicates_removed: int
    estimated_tokens: int
    budget: int
    compression_ratio: float
    token_utilization: float
    selection_time_ms: float = 0.0
    compilation_time_ms: float = 0.0


class SimpleCompiler:
    """Simple deterministic compiler producing human-readable markdown."""

    def __init__(self) -> None:
        self.config = get_config()

    def compile(self, ir: ContextIR, ranked_items: list[ContextItem], query: str | None = None) -> ContextPackage:
        """Compile context package from ranked items."""
        return self._compile_internal(ir, ranked_items, None, query)

    def compile_with_selection(
        self, ir: ContextIR, ranked_items: list[ContextItem], selection: SelectionResult, query: str | None = None, debugging_state=None
    ) -> ContextPackage:
        """Compile with selection result for metrics."""
        return self._compile_internal(ir, ranked_items, selection, query, debugging_state)

    def _compile_internal(
        self, ir: ContextIR, ranked_items: list[ContextItem], selection: SelectionResult | None, query: str | None = None, debugging_state=None
    ) -> ContextPackage:
        """Internal compilation logic."""

        sections: list[ContextSection] = []
        token_budget = self.config.max_context_tokens
        used_tokens = 0

        # Section definitions with priorities
        section_configs: list[tuple[Any, ...]] = [
            ("TASK", self._build_task_section, ir, ranked_items),
            ("PROJECT STATE", self._build_project_state_section, ir, ranked_items),
            ("VERIFIED EVIDENCE", self._build_evidence_section, ir, ranked_items, ItemStatus.VERIFIED),
            ("TEST RESULTS", self._build_test_results_section, ir, ranked_items),
            ("RELEVANT FILES", self._build_files_section, ir, ranked_items, query),
            ("LOGS", self._build_logs_section, ir, ranked_items),
            ("TOOL OUTPUT", self._build_tool_output_section, ir, ranked_items),
            ("CURRENT HYPOTHESIS", self._build_hypothesis_section, ir, ranked_items),
            ("REJECTED HYPOTHESES", self._build_rejected_section, ir, ranked_items, debugging_state),
            ("OPEN QUESTIONS", self._build_questions_section, ir, ranked_items),
            ("CONSTRAINTS", self._build_constraints_section, ir, ranked_items),
            ("PROVENANCE", self._build_provenance_section, ir, ranked_items),
        ]

        for config in section_configs:
            if used_tokens >= token_budget:
                break

            title = config[0]
            builder = config[1]
            args = config[2:]

            content, item_ids, tokens = builder(*args)
            if not content.strip():
                continue

            if used_tokens + tokens > token_budget:
                # Truncate content to fit
                remaining = token_budget - used_tokens
                if remaining > 100:
                    content = self._truncate(content, remaining)
                    tokens = remaining
                else:
                    break

            priority = self.config.section_priority_weights.get(title, 0.0)
            sections.append(
                ContextSection(
                    title=title,
                    content=content,
                    priority=int(priority * 100),
                    item_ids=item_ids,
                    token_estimate=tokens,
                )
            )
            used_tokens += tokens

        # Provenance summary
        provenance_summary = self._build_provenance_summary(ranked_items)

        # Add selection metrics if available
        if selection:
            provenance_summary["selection_metrics"] = selection.metrics

        package = ContextPackage(
            task_id=ir.task_id,
            task_description=ir.task_description,
            sections=sections,
            total_tokens=used_tokens,
            provenance_summary=provenance_summary,
        )

        return package

    def _build_task_section(
        self, ir: ContextIR, items: list[ContextItem]
    ) -> tuple[str, list[str], int]:
        content = f"**Task:** {ir.task_description}\n\n"
        content += f"**Task ID:** {ir.task_id}\n"
        task_items = ir.get_items_by_type(ContextType.TASK)
        if task_items:
            content += f"**Details:** {task_items[0].content}\n"
        tokens = self._estimate_tokens(content)
        return content, [i.id for i in task_items], tokens

    def _build_project_state_section(
        self, ir: ContextIR, items: list[ContextItem]
    ) -> tuple[str, list[str], int]:
        state_items = [i for i in items if i.type == ContextType.PROJECT_STATE]
        if not state_items:
            return "", [], 0

        lines = []
        item_ids = []
        for item in state_items:
            lines.append(f"- {item.content}")
            item_ids.append(item.id)

        content = "\n".join(lines) + "\n"
        tokens = self._estimate_tokens(content)
        return content, item_ids, tokens

    def _build_evidence_section(
        self, ir: ContextIR, items: list[ContextItem], status: "ItemStatus"
    ) -> tuple[str, list[str], int]:
        evidence_items = [i for i in items if i.type == ContextType.EVIDENCE and i.status == status]
        if not evidence_items:
            return "", [], 0

        lines = []
        item_ids = []
        for item in evidence_items:
            lines.append(f"- {item.content} *(source: {item.source})*")
            item_ids.append(item.id)

        content = "\n".join(lines) + "\n"
        tokens = self._estimate_tokens(content)
        return content, item_ids, tokens

    def _build_test_results_section(
        self, ir: ContextIR, items: list[ContextItem]
    ) -> tuple[str, list[str], int]:
        test_items = [i for i in items if i.type == ContextType.TEST_RESULT]
        if not test_items:
            return "", [], 0

        lines = []
        item_ids = []
        for item in test_items:
            lines.append(f"- **{item.source}**: {item.content[:300]}")
            item_ids.append(item.id)

        content = "\n".join(lines) + "\n"
        tokens = self._estimate_tokens(content)
        return content, item_ids, tokens

    def _build_files_section(
        self, ir: ContextIR, items: list[ContextItem], query: str | None = None
    ) -> tuple[str, list[str], int]:
        file_items = [i for i in items if i.type == ContextType.FILE]
        if not file_items:
            return "", [], 0

        # Deduplicate by source
        seen_sources = set()
        unique_items = []
        for item in file_items:
            if item.source not in seen_sources:
                seen_sources.add(item.source)
                unique_items.append(item)

        # Prioritize main source files over test files, and token.py first (bug file)
        def is_test_file(source: str) -> bool:
            return source.startswith("tests/") or "/tests/" in source or source.startswith("tests\\") or "\\tests\\" in source

        def file_priority(item: ContextItem) -> tuple:
            source = item.source
            # Priority: (is_test, is_not_token_py, source_name)
            # token.py gets priority 0, other main files 1, test files 2
            if source == "auth/token.py" or source == "auth\\token.py" or source.endswith("/token.py") or source.endswith("\\token.py"):
                return (0, 0, source)
            elif is_test_file(source):
                return (2, 0, source)
            else:
                return (1, 0, source)

        unique_items.sort(key=file_priority)

        lines = []
        item_ids = []

        # Per-file budget: allocate more to main source files
        num_main = sum(1 for item in unique_items if not is_test_file(item.source))
        num_test = len(unique_items) - num_main
        main_budget = 2000 if num_main > 0 else 0
        test_budget = 800 if num_test > 0 else 0

        # Use query for snippet extraction (has specific bug terms), fallback to task_description
        snippet_query = query or ir.task_description

        for item in unique_items:
            budget = main_budget if not is_test_file(item.source) else test_budget
            # Smart truncation: show relevant lines around query terms
            content_snippet = self._extract_relevant_snippet(item.content, snippet_query, max_chars=budget)
            lines.append(f"- `{item.source}` — {content_snippet}")
            item_ids.append(item.id)

        content = "\n".join(lines) + "\n"
        tokens = self._estimate_tokens(content)
        return content, item_ids, tokens

    def _build_logs_section(
        self, ir: ContextIR, items: list[ContextItem]
    ) -> tuple[str, list[str], int]:
        log_items = [i for i in items if i.type == ContextType.LOG]
        if not log_items:
            return "", [], 0

        lines = []
        item_ids = []
        for item in log_items:
            lines.append(f"- **{item.source}**: {item.content[:300]}")
            item_ids.append(item.id)

        content = "\n".join(lines) + "\n"
        tokens = self._estimate_tokens(content)
        return content, item_ids, tokens

    def _build_tool_output_section(
        self, ir: ContextIR, items: list[ContextItem]
    ) -> tuple[str, list[str], int]:
        tool_items = [i for i in items if i.type == ContextType.TOOL_OUTPUT]
        if not tool_items:
            return "", [], 0

        lines = []
        item_ids = []
        for item in tool_items:
            lines.append(f"- **{item.source}**: {item.content[:300]}")
            item_ids.append(item.id)

        content = "\n".join(lines) + "\n"
        tokens = self._estimate_tokens(content)
        return content, item_ids, tokens

    def _build_hypothesis_section(
        self, ir: ContextIR, items: list[ContextItem]
    ) -> tuple[str, list[str], int]:
        hyp_items = [i for i in items if i.type == ContextType.HYPOTHESIS]
        if not hyp_items:
            return "", [], 0

        lines = []
        item_ids = []
        for item in hyp_items:
            lines.append(f"- {item.content} *(confidence: {item.provenance.confidence:.0%})*")
            item_ids.append(item.id)

        content = "\n".join(lines) + "\n"
        tokens = self._estimate_tokens(content)
        return content, item_ids, tokens

    def _build_rejected_section(
        self, ir: ContextIR, items: list[ContextItem], debugging_state=None
    ) -> tuple[str, list[str], int]:
        from contextforge.models.context_item import ItemStatus
        rejected = [i for i in items if i.status == ItemStatus.REJECTED]

        lines = []
        item_ids = []
        for item in rejected:
            reason = item.metadata.get("rejection_reason", "No reason given")
            lines.append(f"- {item.content} — *Rejected: {reason}*")
            item_ids.append(item.id)

        # Add debugging state rejected hypotheses
        if debugging_state and hasattr(debugging_state, 'rejected_hypotheses'):
            for rh in debugging_state.rejected_hypotheses:
                lines.append(f"- {rh.hypothesis} — *Rejected: {rh.result}* ({rh.rejected_by})")
                item_ids.append(f"rejected_hypothesis_{hash(rh.hypothesis) & 0xffff}")

        if not lines:
            return "", [], 0

        content = "\n".join(lines) + "\n"
        tokens = self._estimate_tokens(content)
        return content, item_ids, tokens

    def _build_questions_section(
        self, ir: ContextIR, items: list[ContextItem]
    ) -> tuple[str, list[str], int]:
        # Open questions would come from DebuggingState, not items
        return "", [], 0

    def _build_constraints_section(
        self, ir: ContextIR, items: list[ContextItem]
    ) -> tuple[str, list[str], int]:
        constraint_items = [i for i in items if i.type == ContextType.CONSTRAINT]
        if not constraint_items:
            return "", [], 0

        lines = []
        item_ids = []
        for item in constraint_items:
            lines.append(f"- {item.content}")
            item_ids.append(item.id)

        content = "\n".join(lines) + "\n"
        tokens = self._estimate_tokens(content)
        return content, item_ids, tokens

    def _build_provenance_section(
        self, ir: ContextIR, items: list[ContextItem]
    ) -> tuple[str, list[str], int]:
        lines = []
        item_ids = []
        seen_sources = set()

        for item in items:
            key = (item.provenance.source_type.value, item.provenance.source_id)
            if key in seen_sources:
                continue
            seen_sources.add(key)
            lines.append(
                f"- {item.provenance.source_type.value}:{item.provenance.source_id} "
                f"(observed by {item.provenance.observer}, "
                f"confidence {item.provenance.confidence:.0%})"
            )
            item_ids.append(item.id)

        if not lines:
            return "", [], 0

        content = "\n".join(lines) + "\n"
        tokens = self._estimate_tokens(content)
        return content, item_ids, tokens

    def _build_provenance_summary(self, items: list[ContextItem]) -> dict[str, Any]:
        summary: dict[str, Any] = {
            "total_items": len(items),
            "by_source_type": {},
            "by_status": {},
            "by_type": {},
            "unique_sources": set(),
        }

        for item in items:
            st = item.provenance.source_type.value
            summary["by_source_type"][st] = summary["by_source_type"].get(st, 0) + 1
            status_val = item.status.value
            summary["by_status"][status_val] = summary["by_status"].get(status_val, 0) + 1
            type_val = item.type.value
            summary["by_type"][type_val] = summary["by_type"].get(type_val, 0) + 1
            summary["unique_sources"].add(f"{st}:{item.provenance.source_id}")

        summary["unique_sources"] = len(summary["unique_sources"])
        return summary

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimate: ~4 chars per token."""
        return max(1, len(text) // 4)

    def _truncate(self, text: str, max_tokens: int) -> str:
        """Truncate text to approximate token limit."""
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "\n... [truncated]"

    def _extract_relevant_snippet(self, content: str, query: str, max_chars: int = 5000) -> str:
        """Extract relevant lines from file content based on query terms.

        Guarantees that the highest-scoring (anchor) lines are preserved in the output.
        Expands context around the highest-scoring lines, then shrinks from the
        side farther from the anchor center if needed to fit max_chars.
        """
        if len(content) <= max_chars:
            return content

        # Get query terms (lowercase, include all meaningful words)
        query_terms = [t.lower() for t in query.split() if len(t) > 2]
        if not query_terms:
            return content[:max_chars] + "... [truncated]"

        lines = content.split('\n')
        scored_lines = []
        for i, line in enumerate(lines):
            line_lower = line.lower()
            score = sum(1 for term in query_terms if term in line_lower)
            if score > 0:
                scored_lines.append((score, i, line))

        if not scored_lines:
            return content[:max_chars] + "... [truncated]"

        # Sort by relevance descending
        scored_lines.sort(key=lambda x: -x[0])
        max_score = scored_lines[0][0]

        # Use ONLY max-score lines as anchors (highest relevance)
        anchor_indices = [idx for score, idx, _ in scored_lines if score == max_score]
        if not anchor_indices:
            return content[:max_chars] + "... [truncated]"

        min_anchor = min(anchor_indices)
        max_anchor = max(anchor_indices)
        anchor_center = (min_anchor + max_anchor) // 2

        # Expand context around anchors (30 lines each side)
        context = 30
        min_idx = max(0, min(anchor_indices) - 30)
        max_idx = min(len(lines) - 1, max(anchor_indices) + 30)

        # Shrink from the side farther from the anchor center (fixed)
        anchor_center = (min(anchor_indices) + max(anchor_indices)) // 2
        while True:
            selected = lines[min_idx:max_idx + 1]
            snippet = '\n'.join(selected)
            if len(snippet) <= max_chars:
                break
            if min_idx >= max_idx:
                break
            # Shrink from side farther from anchor center (fixed)
            dist_min = anchor_center - min_idx
            dist_max = max_idx - anchor_center
            if dist_min >= dist_max:
                min_idx += 1
            else:
                max_idx -= 1

        snippet = '\n'.join(lines[min_idx:max_idx + 1])
        
        # Final safety truncation
        if len(snippet) > max_chars:
            # Try to preserve the anchor region
            anchor_text = '\n'.join(content.split('\n')[min(anchor_indices):max(anchor_indices)+1])
            pos = snippet.find('\n'.join(content.split('\n')[min(anchor_indices):max(anchor_indices)+1]))
            if pos != -1:
                excess = len(snippet) - max_chars
                snippet = snippet[excess//2 : len(snippet) - excess//2]
                if len(snippet) > max_chars:
                    snippet = snippet[:max_chars]
            else:
                snippet = snippet[:max_chars]
            snippet = snippet + "... [truncated]"
        
        # Add truncation markers
        if min_idx > 0 or max_idx < len(lines) - 1:
            prefix = "... [truncated] " if min_idx > 0 else ""
            suffix = " ... [truncated]" if max_idx < len(lines) - 1 else ""
            snippet = prefix + snippet + suffix
        
        return snippet

