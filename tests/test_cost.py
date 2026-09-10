from demo.cost import estimate_cost_usd, estimate_tokens


def test_local_is_zero():
    assert estimate_cost_usd(route_model="local", prompt="hi", completion="there") == 0.0
    assert estimate_cost_usd(route_model="ollama/qwen2.5:0.5b", prompt="hi", completion="x") == 0.0


def test_cloud_uses_list_prices():
    cost = estimate_cost_usd(
        route_model="cloud",
        prompt="x",
        completion="y",
        prompt_tokens=1_000_000,
        completion_tokens=1_000_000,
    )
    assert abs(cost - 4.50) < 1e-9


def test_token_heuristic():
    assert estimate_tokens("") == 0
    assert estimate_tokens("abcd") == 1
