#!/usr/bin/env python3
"""Add _extract_relevant_snippet method to SimpleCompiler class."""

with open('src/contextforge/compilation/base.py', 'r') as f:
    content = f.read()

# Find the end of SimpleCompiler class (before next class or end of file)
class_pos = content.find('class ', content.find('class SimpleCompiler') + 20)
if class_pos == -1:
    insert_pos = len(content)
else:
    insert_pos = class_pos

new_method = "\n    def _extract_relevant_snippet(self, content: str, query: str, max_chars: int = 5000) -> str:\n        \"\"\"Extract relevant lines from file content based on query terms.\n\n        Guarantees that the highest-scoring (anchor) lines are preserved in the output.\n        Expands context around the highest-scoring lines, then shrinks from the\n        side farther from the anchor center if needed to fit max_chars.\n        \"\"\"\n        if len(content) <= max_chars:\n            return content\n\n        # Get query terms (lowercase, include all meaningful words)\n        query_terms = [t.lower() for t in query.split() if len(t) > 2]\n        if not query_terms:\n            return content[:max_chars] + \"... [truncated]\"\n\n        lines = content.split('\\n')\n        scored_lines = []\n        for i, line in enumerate(lines):\n            line_lower = line.lower()\n            score = sum(1 for term in query_terms if term in line_lower)\n            if score > 0:\n                scored_lines.append((score, i, line))\n\n        if not scored_lines:\n            return content[:max_chars] + \"... [truncated]\"\n\n        # Sort by relevance descending\n        scored_lines.sort(key=lambda x: -x[0])\n        max_score = scored_lines[0][0]\n\n        # Use ONLY max-score lines as anchors (highest relevance)\n        anchor_indices = [idx for score, idx, _ in scored_lines if score == max_score]\n        if not anchor_indices:\n            return content[:max_chars] + \"... [truncated]\"\n\n        min_anchor = min(anchor_indices)\n        max_anchor = max(anchor_indices)\n        anchor_center = (min_anchor + max_anchor) // 2\n\n        # Expand context around anchors (30 lines each side)\n        context = 30\n        min_idx = max(0, min(anchor_indices) - 30)\n        max_idx = min(len(lines) - 1, max(anchor_indices) + 30)\n\n        # Shrink from the side farther from the anchor center (fixed)\n        anchor_center = (min(anchor_indices) + max(anchor_indices)) // 2\n        while True:\n            selected = lines[min_idx:max_idx + 1]\n            snippet = '\\n'.join(selected)\n            if len(snippet) <= max_chars:\n                break\n            if min_idx >= max_idx:\n                break\n            # Shrink from side farther from anchor center (fixed)\n            dist_min = anchor_center - min_idx\n            dist_max = max_idx - anchor_center\n            if dist_min >= dist_max:\n                min_idx += 1\n            else:\n                max_idx -= 1\n\n        snippet = '\\n'.join(lines[min_idx:max_idx + 1])\n        \n        # Final safety truncation\n        if len(snippet) > max_chars:\n            # Try to preserve the anchor region\n            anchor_text = '\\n'.join(content.split('\\n')[min(anchor_indices):max(anchor_indices)+1])\n            pos = snippet.find('\\n'.join(content.split('\\n')[min(anchor_indices):max(anchor_indices)+1]))\n            if pos != -1:\n                excess = len(snippet) - max_chars\n                snippet = snippet[excess//2 : len(snippet) - excess//2]\n                if len(snippet) > max_chars:\n                    snippet = snippet[:max_chars]\n            else:\n                snippet = snippet[:max_chars]\n            snippet = snippet + \"... [truncated]\"\n        \n        # Add truncation markers\n        if min_idx > 0 or max_idx < len(lines) - 1:\n            prefix = \"... [truncated] \" if min_idx > 0 else \"\"\n            suffix = \" ... [truncated]\" if max_idx < len(lines) - 1 else \"\"\n            snippet = prefix + snippet + suffix\n        \n        return snippet\n"

# Find the end of SimpleCompiler class (before next class or end of file)
class_pos = content.find('class ', content.find('class SimpleCompiler') + 20)
if class_pos == -1:
    insert_pos = len(content)
else:
    insert_pos = class_pos

new_content = content[:insert_pos] + '\n' + new_method + '\n' + content[insert_pos:]

with open('src/contextforge/compilation/base.py', 'w') as f:
    f.write(new_content)
print('Added _extract_relevant_snippet method')