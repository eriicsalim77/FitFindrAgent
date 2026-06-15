from tools import create_fit_card, search_listings, suggest_outfit
from utils.data_loader import get_example_wardrobe


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


def test_suggest_outfit_empty_wardrobe():
    new_item = {
        "title": "Vintage Band Tee",
        "category": "tops",
        "style_tags": ["vintage", "graphic"],
        "colors": ["black"],
    }
    result = suggest_outfit(new_item, {"items": []})
    assert isinstance(result, str)
    assert len(result) > 0


def test_suggest_outfit_with_wardrobe():
    new_item = {
        "title": "Vintage Band Tee",
        "category": "tops",
        "style_tags": ["vintage", "graphic"],
        "colors": ["black"],
    }
    result = suggest_outfit(new_item, get_example_wardrobe())
    assert isinstance(result, str)
    assert len(result) > 0


def test_suggest_outfit_references_wardrobe_items():
    new_item = {
        "title": "Vintage Band Tee",
        "category": "tops",
        "style_tags": ["vintage", "graphic"],
        "colors": ["black"],
    }
    wardrobe = get_example_wardrobe()
    result = suggest_outfit(new_item, wardrobe)

    result_lower = result.lower()
    assert any(
        item["name"].lower() in result_lower for item in wardrobe["items"]
    )


def test_create_fit_card_returns_string():
    new_item = {
        "title": "Vintage Band Tee",
        "price": 22.0,
        "platform": "depop",
        "category": "tops",
        "style_tags": ["vintage", "graphic"],
        "colors": ["black", "white"],
        "condition": "good",
    }
    outfit = "Pair with wide-leg jeans and chunky sneakers for a 90s vibe."
    result = create_fit_card(outfit, new_item)
    assert isinstance(result, str)
    assert len(result) > 0


def test_create_fit_card_empty_outfit():
    new_item = {
        "title": "Vintage Band Tee",
        "price": 22.0,
        "platform": "depop",
        "category": "tops",
        "style_tags": ["vintage", "graphic"],
        "colors": ["black", "white"],
        "condition": "good",
    }
    result = create_fit_card("", new_item)
    assert isinstance(result, str)
    assert "empty" in result.lower()


def test_create_fit_card_whitespace_outfit():
    new_item = {
        "title": "Vintage Band Tee",
        "price": 22.0,
        "platform": "depop",
        "category": "tops",
        "style_tags": ["vintage", "graphic"],
        "colors": ["black", "white"],
        "condition": "good",
    }
    result = create_fit_card("   ", new_item)
    assert isinstance(result, str)
    assert "empty" in result.lower()
