from hashlib import sha256

MAX_NODE_NAME_LENGTH = 120


def suffixed_node_name(base: str, suffix: str) -> str:
    candidate = f"{base} – {suffix}"
    if len(candidate) <= MAX_NODE_NAME_LENGTH:
        return candidate
    digest = sha256(base.encode("utf-8")).hexdigest()[:8]
    ending = f" – {digest} – {suffix}"
    return f"{base[: MAX_NODE_NAME_LENGTH - len(ending)]}{ending}"