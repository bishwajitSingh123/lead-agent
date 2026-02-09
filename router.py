# router.py

def route_request(user_message: str) -> str:
    msg = user_message.lower()

    # 1. rule based → avoid LLM
    trivial_patterns = [
        "hi",
        "hello",
        "thanks",
        "thank you",
        "bye"
    ]

    if any(p in msg for p in trivial_patterns):
        return "rule_based"

    # 2. heavy reasoning → big model
    heavy_patterns = [
        "analyze",
        "compare",
        "research",
        "plan",
        "strategy",
        "summarize document"
    ]

    if any(p in msg for p in heavy_patterns):
        return "big_model"

    # 3. default → small model
    return "small_model"
