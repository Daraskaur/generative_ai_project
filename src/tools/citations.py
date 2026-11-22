"""
Build a "Sources" footer showing which document and pages an answer came from.
"""

from src.rag.retriever_setup import get_source_references


def build_citation_footer(result: dict) -> str:
    """
    Create a markdown footer listing the files and pages used for an answer.

    Args:
        result: The final state returned by the graph (has route and latest_query).

    Returns:
        A markdown string, or an empty string when there is nothing to cite.
    """
    try:
        # Only document answers have sources to cite
        if result.get("route") != "index":
            return ""

        # A "not found" answer used no sources, so it gets no citation
        answer_text = str(result["messages"][-1].content).lower()
        if "could not find this information" in answer_text:
            return ""

        query = result.get("latest_query")
        if not query:
            return ""

        references = get_source_references(query)
        if not references:
            return ""

        # Group page numbers by file, keeping the order files first appear
        pages_by_file = {}
        for item in references:
            pages = pages_by_file.setdefault(item["file"], [])
            if item["page"] is not None and item["page"] not in pages:
                pages.append(item["page"])

        lines = []
        for file_name, pages in pages_by_file.items():
            if pages:
                pages.sort()
                label = "page" if len(pages) == 1 else "pages"
                page_text = ", ".join(str(p) for p in pages)
                lines.append(f"- {file_name} — {label} {page_text}")
            else:
                lines.append(f"- {file_name}")

        return "\n\n📄 **Sources:**\n" + "\n".join(lines)
    except Exception as e:
        print("Could not build citations:", e)
        return ""