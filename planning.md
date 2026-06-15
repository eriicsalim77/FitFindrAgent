# FitFindr — planning.md

## Tools

### Tool 1: search_listings

**What it does:**

Searches the mock listings dataset based on the user's description and filter criteria, then returns the top matching items sorted by relevance.

**Input parameters:**

- `description` (str): A natural language description of what the user is looking for. The tool matches this against the title, description, and style_tags fields of each listing.
- `size` (str, optional): Filter by size (e.g. "S", "M", "L", "XL"). If None, no size filter is applied.
- `max_price` (float, optional): Filter to only items priced at or below this value. If None, no price filter is applied.

**What it returns:**

A list of up to 3 listing dictionaries sorted by relevance to the description. Each dictionary has the following fields: `id` (str), `title` (str), `description` (str), `category` (str), `style_tags` (list[str]), `size` (str), `condition` (str), `price` (float), `colors` (list[str]), `brand` (str or None), `platform` (str). Returns an empty list if no listings match the filters.

**What happens if it fails or returns nothing:**

If the returned list is empty, the agent does not call suggest_outfit. Instead, it tells the user: "I couldn't find any listings matching that. Try widening your price range, removing the size filter, or using different keywords." The chain stops here and waits for a new user query.

---

### Tool 2: suggest_outfit

**What it does:**

Takes a new item the user is considering buying and pairs it with pieces from their existing wardrobe to produce a complete outfit recommendation.

**Input parameters:**

- `new_item` (dict): The selected listing from search_listings, containing fields like title, category, style_tags, and colors. This is the item we are styling around.
- `wardrobe` (dict): The user's current wardrobe, with an `items` key holding a list of wardrobe item dictionaries (each with name, category, colors, style_tags, and other styling-relevant fields).

**What it returns:**

A string describing how to style the new item with specific pieces from the wardrobe. Example: "Pair this with your wide-leg jeans and platform Docs for a 90s grunge look. Roll the sleeves once and tuck the front corner."

**What happens if it fails or returns nothing:**

If the wardrobe is empty, the agent tells the user: "I'd suggest you upload your wardrobe first so I can recommend a specific outfit." The chain stops here. If the wardrobe has items but the model returns nothing usable, the agent falls back to suggesting general styling guidance based on the new item alone.

---

### Tool 3: create_fit_card

**What it does:**

Generates a short, social-media-style caption celebrating the new thrifted item within the context of the suggested outfit. The output is meant to feel like something a user would post on Instagram or Depop.

**Input parameters:**

- `outfit` (str): The styling recommendation returned by suggest_outfit.
- `new_item` (dict): The selected listing from search_listings, so the caption can reference the specific piece, price, and platform.

**What it returns:**

A short caption string (1-3 sentences) that highlights the new item and references the broader outfit. Example: "thrifted this faded band tee off depop for $22 and honestly it was made for my wide-legs 🖤 full look in my stories"

**What happens if it fails or returns nothing:**

If outfit or new_item is missing or incomplete, the agent returns a generic fallback: "I found you this item but couldn't generate a caption right now. Try again or write your own." The agent still surfaces the listing and outfit suggestion so the interaction isn't wasted.

---

## Planning Loop

**How does your agent decide which tool to call next?**

The loop runs in a fixed sequence with conditional branches:

1. Receive the user query.
2. Call `search_listings(description, size, max_price)` with parameters extracted from the user message.
3. Check the result: if the returned list is empty, set an error message in the session and return early. Do not proceed to suggest_outfit.
4. If results exist, set `selected_item = results[0]` (top match) in the session.
5. Call `suggest_outfit(new_item=selected_item, wardrobe=user_wardrobe)`.
6. Check the result: if the wardrobe is empty, set an error message and return early. If a suggestion is returned, save it as `outfit_suggestion` in the session.
7. Call `create_fit_card(outfit=outfit_suggestion, new_item=selected_item)`.
8. Save the result as `fit_card` in the session.
9. Return the full session (selected_item, outfit_suggestion, fit_card) to the user.

The agent is done when either all three tools complete successfully, or one of the early-exit error conditions fires.

---

## State Management

**How does information from one tool get passed to the next?**

The agent uses a session dictionary that accumulates as tools run. After each tool call, the output is stored in the session before the next tool is invoked.

Session keys:
- `user_query` (str): the original user message
- `selected_item` (dict or None): top result from search_listings
- `outfit_suggestion` (str or None): output from suggest_outfit
- `fit_card` (str or None): output from create_fit_card
- `error` (str or None): set when any tool fails or returns nothing, ends the loop

Each tool reads only the session keys it needs as input parameters, so tools stay decoupled and testable on their own. The session is the single source of truth for what has happened so far in the interaction.

---

## Error Handling

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | "I couldn't find any listings matching that. Try widening your price range, removing the size filter, or using different keywords." Stop the chain. |
| suggest_outfit | Wardrobe is empty | "I'd suggest you upload your wardrobe first so I can recommend a specific outfit." Stop the chain. |
| create_fit_card | Outfit input is missing or incomplete | "I found you this item but couldn't generate a caption right now. Try again or write your own." Still surface the listing and outfit suggestion. |

---

## Architecture

\`\`\`
User query
    │
    ▼
Planning Loop ──────────────────────────────────────────────┐
    │                                                       │
    ├─► search_listings(description, size, max_price)       │
    │       │ results=[]                                    │
    │       ├──► [ERROR] "No listings found..." → return ───┤
    │       │                                               │
    │       │ results=[item, ...]                           │
    │       ▼                                               │
    │   Session: selected_item = results[0]                 │
    │       │                                               │
    ├─► suggest_outfit(selected_item, wardrobe)             │
    │       │ wardrobe empty                                │
    │       ├──► [ERROR] "Upload your wardrobe..." → return ┤
    │       │                                               │
    │       │ suggestion=string                             │
    │       ▼                                               │
    │   Session: outfit_suggestion = "..."                  │
    │       │                                               │
    └─► create_fit_card(outfit_suggestion, selected_item)   │
            │                                               │
        Session: fit_card = "..."                           │
            │                                               └─ error path returns here
            ▼
        Return session to user
\`\`\`

---

## AI Tool Plan

**Milestone 3 — Individual tool implementations:**

I'll use Claude Code for each of the three tool implementations. For each tool, I'll share the corresponding Tool block from this planning.md (inputs, return value, failure mode) plus the data_loader.py helper functions.

- For `search_listings`, I'll ask Claude to implement filtering on size and max_price using load_listings(), then to rank remaining results by relevance to the description. Before trusting it, I'll test with 3 queries: one that should return results, one with too-strict filters that should return [], and one with no filters at all.
- For `suggest_outfit`, I'll ask Claude to construct a prompt that combines new_item and wardrobe context, calls Groq's Llama 3.3, and returns the styling string. I'll verify it handles empty wardrobes by returning the right error signal.
- For `create_fit_card`, I'll ask Claude to write a prompt that produces a casual social caption, then test the output for tone (it should feel like a Depop caption, not a press release).

**Milestone 4 — Planning loop and state management:**

I'll give Claude my Planning Loop section, State Management section, and the architecture diagram. I'll ask Claude to implement the orchestrator function that calls each tool in sequence, updates the session dict, and handles the two early-exit branches (empty search results, empty wardrobe). Before trusting it, I'll trace through the example query in this planning.md and confirm the session evolves correctly at each step. I'll also test the two error paths to confirm the chain stops where it should.

---

## A Complete Interaction (Step by Step)

FitFindr is an AI agent that helps users search for a thrifted item and figure out how to wear it. The agent runs three tools in sequence: search_listings → suggest_outfit → create_fit_card. If search_listings returns 0 results, the chain stops and the agent asks the user to adjust their query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**

The agent extracts parameters from the user message and calls `search_listings(description="vintage graphic tee", size=None, max_price=30.0)`. The tool returns a list of 3 matching listings. The top result is saved to session: `selected_item = {title: "Faded Band Tee", price: 22.0, platform: "depop", condition: "good", ...}`.

**Step 2:**

The agent calls `suggest_outfit(new_item=selected_item, wardrobe=user_wardrobe)` where user_wardrobe contains the user's baggy jeans and chunky sneakers. The tool returns the styling string: "Pair this with your wide-leg jeans and platform Docs for a classic 90s grunge look. Roll the sleeves once and tuck the front corner slightly for shape." This is saved to session as `outfit_suggestion`.

**Step 3:**

The agent calls `create_fit_card(outfit=outfit_suggestion, new_item=selected_item)`. The tool returns: "thrifted this faded band tee off depop for $22 and honestly it was made for my wide-legs 🖤 full look in my stories". This is saved to session as `fit_card`.

**Final output to user:**

The user sees the selected listing details (title, price, platform, condition), the outfit suggestion describing how to style it with their existing wardrobe, and the social caption they can use when posting about the new piece.