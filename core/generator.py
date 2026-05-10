import json
import os
import urllib.request

from core.retriever import Source


def _build_prompt(question: str, sources: list[Source]) -> str:
    # Step 5: numbered context blocks so the LLM can cite by [1], [2], etc.
    context_blocks = "\n\n".join(
        f'[{i+1}] (from: "{s["source"]}", ingested: {s["date"]})\n{s["text"]}'
        for i, s in enumerate(sources)
    )
    return f"""You are a personal knowledge assistant. Answer based ONLY on the context below.
If the answer is not in the context, say "I don't have notes on that."
Always cite which source you used as [1], [2], etc.

Context:
{context_blocks}

Question: {question}

Answer:"""


def generate(question: str, sources: list[Source]) -> str:
    # Step 6: raw POST to OpenAI chat completions — no SDK
    api_key = os.environ["OPENAI_API_KEY"]
    prompt  = _build_prompt(question, sources)

    payload = json.dumps({
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,   # low temperature = more factual, less hallucination
        "max_tokens": 512,
    }).encode()

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())

    return data["choices"][0]["message"]["content"].strip()
