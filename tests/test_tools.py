from tools import search_listings


def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) >= 1


def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []


def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=100)
    assert all(item["price"] <= 100 for item in results)


def test_search_size_filter_case_insensitive():
    results = search_listings("tee", size="m", max_price=None)
    assert all("m" in item["size"].lower() for item in results)


def test_search_max_results_capped_at_3():
    results = search_listings("vintage", size=None, max_price=None)
    assert len(results) <= 3
