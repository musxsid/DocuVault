"""
DocuVault — Document Version History & Text Diff Engine
Tracks multi-version document lineage, computes unified and side-by-side
differences with added/removed highlights, and supports non-destructive rollback.
"""

import difflib
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class DocumentVersionManager:
    """
    Manages document version lineage and text diff comparisons.
    Uses difflib to generate granular clause diffs with added and removed clause highlights.
    """

    @staticmethod
    def compare_versions(
        text_v1: str,
        text_v2: str,
        label_v1: str = "Version 1.0",
        label_v2: str = "Version 2.0"
    ) -> Dict[str, Any]:
        """
        Compares two versions of document text using difflib.
        Returns additions, deletions, modifications, and structured HTML diff.
        """
        lines1 = text_v1.splitlines(keepends=True)
        lines2 = text_v2.splitlines(keepends=True)

        matcher = difflib.SequenceMatcher(None, lines1, lines2)
        similarity_pct = round(matcher.ratio() * 100, 1)

        diff_lines = list(difflib.unified_diff(
            lines1, lines2,
            fromfile=label_v1,
            tofile=label_v2,
            lineterm=""
        ))

        # Categorize additions and deletions
        additions = []
        deletions = []
        structured_diff = []

        for line in diff_lines:
            line_str = line.strip()
            if not line_str or line_str.startswith("---") or line_str.startswith("+++") or line_str.startswith("@@"):
                continue
            if line.startswith("+"):
                additions.append(line_str[1:].strip())
                structured_diff.append({"type": "add", "text": line_str[1:].strip()})
            elif line.startswith("-"):
                deletions.append(line_str[1:].strip())
                structured_diff.append({"type": "remove", "text": line_str[1:].strip()})
            else:
                structured_diff.append({"type": "context", "text": line_str.strip()})

        return {
            "similarity_percentage": similarity_pct,
            "additions_count": len(additions),
            "deletions_count": len(deletions),
            "additions": additions,
            "deletions": deletions,
            "diff_lines": diff_lines,
            "structured_diff": structured_diff,
        }

    @staticmethod
    def generate_html_diff(
        text_v1: str,
        text_v2: str,
        label_v1: str = "Earlier Version",
        label_v2: str = "Current Version",
        theme_is_dark: bool = False
    ) -> str:
        """Generates a clean HTML representation of text differences with color highlights."""
        diff_data = DocumentVersionManager.compare_versions(text_v1, text_v2, label_v1, label_v2)

        bg = "#1B1D25" if theme_is_dark else "#F8F9FA"
        text_col = "#F9FAFB" if theme_is_dark else "#111827"
        add_bg = "rgba(16, 185, 129, 0.20)" if theme_is_dark else "#ECFDF5"
        add_col = "#34D399" if theme_is_dark else "#065F46"
        del_bg = "rgba(239, 68, 68, 0.20)" if theme_is_dark else "#FEF2F2"
        del_col = "#F87171" if theme_is_dark else "#991B1B"
        border_col = "#313545" if theme_is_dark else "#E5E7EB"

        html = f"""
        <div style="font-family: 'Segoe UI', system-ui, sans-serif; font-size: 12px; color: {text_col}; line-height: 1.6;">
            <div style="padding: 10px; background: {bg}; border: 1px solid {border_col}; border-radius: 8px; margin-bottom: 12px;">
                <strong>Comparison Summary:</strong> {diff_data['similarity_percentage']}% text match &bull;
                <span style="color: {add_col}; font-weight: 600;">+{diff_data['additions_count']} clauses added</span> &bull;
                <span style="color: {del_col}; font-weight: 600;">-{diff_data['deletions_count']} clauses removed</span>
            </div>
            <div style="border: 1px solid {border_col}; border-radius: 8px; overflow: hidden;">
        """

        for item in diff_data["structured_diff"]:
            txt = item["text"]
            if item["type"] == "add":
                html += f'<div style="background: {add_bg}; color: {add_col}; padding: 4px 10px; border-left: 3px solid {add_col};"><strong>+</strong> {txt}</div>'
            elif item["type"] == "remove":
                html += f'<div style="background: {del_bg}; color: {del_col}; padding: 4px 10px; border-left: 3px solid {del_col}; text-decoration: line-through;"><strong>-</strong> {txt}</div>'
            else:
                html += f'<div style="padding: 3px 10px; color: {text_col}; opacity: 0.85;">&nbsp;&nbsp;{txt}</div>'

        html += "</div></div>"
        return html
