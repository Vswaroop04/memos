
def chunk(
    text: str,
    max_chars: int = 512,
    overlap: int = 50
) -> list[dict]:

    blocks = text.split("\n\n")

    chunks = []
    idx = 0

    for block in blocks:

        block = block.strip()

        if not block:
            continue

        lines = block.splitlines()

        is_table = True

        for line in lines:

            if not line.strip():
                continue

            if not line.strip().startswith("|"):
                is_table = False
                break

        if is_table:
            chunks.append({
                "text": block,
                "index": idx,
                "type": "table"
            })

            idx += 1
            continue

        if len(block) <= max_chars:

            chunks.append({
                "text": block,
                "index": idx,
                "type": "text"
            })

            idx += 1
            continue

        start = 0

        while start < len(block):

            end = start + max_chars

            piece = block[start:end]

            chunks.append({
                "text": piece,
                "index": idx,
                "type": "text"
            })

            idx += 1

            start = end - overlap

    return chunks