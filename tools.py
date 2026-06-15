"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    listings = load_listings()

    if max_price is not None:
        listings = [item for item in listings if item["price"] <= max_price]

    if size is not None:
        size_lower = size.lower()
        listings = [
            item for item in listings if size_lower in item["size"].lower()
        ]

    keywords = description.lower().split()

    scored = []
    for item in listings:
        haystack = " ".join(
            [item["title"], item["description"], " ".join(item["style_tags"])]
        ).lower().split()
        score = sum(1 for word in keywords if word in haystack)
        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda pair: pair[0], reverse=True)

    return [item for _, item in scored[:3]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    client = _get_groq_client()

    item_description = (
        f"Title: {new_item['title']}\n"
        f"Category: {new_item['category']}\n"
        f"Colors: {', '.join(new_item['colors'])}\n"
        f"Style tags: {', '.join(new_item['style_tags'])}"
    )

    wardrobe_items = wardrobe.get("items", [])

    if not wardrobe_items:
        system_message = (
            "You are a fashion stylist helping a user style a new thrifted "
            "find. They haven't shared their wardrobe yet. Give 1-2 outfit "
            "ideas describing what kinds of pieces pair well, the vibe, and "
            "a quick color palette. Be specific and practical."
        )
        user_message = (
            f"Here's the new item:\n{item_description}\n\n"
            "Suggest what kinds of pieces would pair well with this item."
        )
    else:
        system_message = (
            "You are a fashion stylist. The user has a new thrifted find "
            "and an existing wardrobe. Suggest 1-2 complete outfits using "
            "the new item paired with specific named pieces from their "
            "wardrobe. Reference wardrobe pieces by their 'name' field. Be "
            "specific about styling tips."
        )
        wardrobe_list = "\n".join(
            f"- {wardrobe_item['name']} ({wardrobe_item['category']})"
            for wardrobe_item in wardrobe_items
        )
        user_message = (
            f"Here's the new item:\n{item_description}\n\n"
            f"Here's my current wardrobe:\n{wardrobe_list}\n\n"
            "Suggest 1-2 outfits that combine the new item with specific "
            "pieces from my wardrobe, referencing them by name."
        )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0.7,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
    )

    return response.choices[0].message.content.strip()


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    if not outfit or not outfit.strip():
        return (
            "Couldn't generate a caption — the outfit input was empty. "
            "Showing you the item and outfit suggestion instead."
        )

    client = _get_groq_client()

    system_message = (
        "You are writing a casual, authentic Instagram or Depop caption for "
        "someone showing off their thrifted find. Match the vibe of real "
        "fashion creators — casual, specific, a little playful. Mention the "
        "item, price, and platform naturally (don't list them like a "
        "product description). Reference the outfit vibe. Keep it 2-4 "
        "sentences. No hashtags unless they feel natural. Lowercase is fine."
    )

    user_message = (
        f"Item: {new_item['title']}\n"
        f"Price: ${new_item['price']}\n"
        f"Platform: {new_item['platform']}\n"
        f"Condition: {new_item['condition']}\n"
        f"Colors: {', '.join(new_item['colors'])}\n\n"
        f"Outfit suggestion:\n{outfit}\n\n"
        "Write the caption now."
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0.9,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
    )

    return response.choices[0].message.content.strip()
