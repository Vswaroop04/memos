import trafilatura


def load(url: str) -> str:
    downloaded = trafilatura.fetch_url(url)
    text = trafilatura.extract(downloaded, include_tables=True, output_format="markdown")
    if not text:
        raise ValueError(f"Could not extract content from {url}")
    return text
