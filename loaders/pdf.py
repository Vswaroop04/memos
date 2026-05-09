import pymupdf4llm


def load(path: str) -> str:
    # Converts PDF to markdown, preserving tables as markdown tables
    return pymupdf4llm.to_markdown(path)
