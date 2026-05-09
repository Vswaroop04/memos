import json
import os
import urllib.request


def embed(texts: list[str]) -> list[list[float]]:
    api_key = os.environ["OPENAI_API_KEY"]
    payload = json.dumps({
        "input": texts,
        "model": "text-embedding-3-small",
    }).encode()

    req = urllib.request.Request(
        "https://api.openai.com/v1/embeddings",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())

    # API may return items out of order — sort by index to match input order
    items = sorted(data["data"], key=lambda x: x["index"])
    return [item["embedding"] for item in items]
