# FitFindr 🛍️

AI agent that helps you find secondhand clothing and figure out how to wear it.

Type a query like *"vintage graphic tee under $30, size M"* and the agent searches the listings, picks a match, suggests an outfit using your wardrobe, and writes a casual fit card caption.

Built for CodePath AI201, Project 2.

---

## How it works

Three tools chained together. The middle step only runs if the first one finds something.

User query
   │
   ▼
search_listings  ──►  no results?  ──►  stop, show helpful error
   │
   ▼
suggest_outfit  ──►  picks pieces from your wardrobe
   │
   ▼
create_fit_card  ──►  writes the caption
   │
   ▼
Show the user```


## The 3 tools

### `search_listings(description, size, max_price)`

Filters the mock listings dataset by keywords and optional size or price ceiling. Returns up to 3 dicts sorted by relevance, or `[]` if nothing matches.

### `suggest_outfit(new_item, wardrobe)`

Calls Llama 3.3 to suggest outfits using the new item and pieces from the user's wardrobe by name. If the wardrobe is empty, returns general styling advice instead. Temperature 0.7.

### `create_fit_card(outfit, new_item)`

Calls Llama 3.3 again to write a casual Instagram-style caption (2-4 sentences). Returns a fallback string if `outfit` is empty. Temperature 0.9 for variety.

---

## The planning loop

Lives in `agent.py`. Numbered steps:

1. Initialize a session dict that holds all state for the interaction.
2. Parse the query with regex. Pull out `description`, `size`, `max_price`.
3. Call `search_listings`. If it returns `[]`, set an error message and **stop** — never call the downstream tools with empty input.
4. Save the top result as `selected_item`.
5. Call `suggest_outfit`. Save the output as `outfit_suggestion`.
6. Call `create_fit_card`. Save the output as `fit_card`.
7. Return the session.

The branching at step 3 is the main thing that makes this an agent and not just a script. The agent decides whether to keep going based on what just happened.

---

## State management

One session dict holds everything for an interaction. Each tool reads only what it needs, then writes its output back. The session is the single source of truth.

Keys: `query`, `parsed`, `search_results`, `selected_item`, `wardrobe`, `outfit_suggestion`, `fit_card`, `error`.

If `error` is set, the interaction ended early and the other output fields are `None`.

---

## Error handling

| Tool | Failure | What happens |
|------|--------|---------|
| `search_listings` | No matches | Set `session["error"]` with a helpful message, stop the chain |
| `suggest_outfit` | Empty wardrobe | Tool returns general styling advice (no crash, chain continues) |
| `create_fit_card` | Empty outfit string | Returns a fallback caption (no LLM call wasted) |

**Concrete example:** Query `"designer ballgown size XXS under $5"` → `search_listings` returns `[]` → agent stops → UI shows the helpful error in the first panel and leaves the other two blank.

Screenshot: `failure_demo.png` in the repo root.

---

## Spec reflection

**What the spec got right:** Writing planning.md first forced me to decide what the agent does when `search_listings` returns nothing. That decision shaped the whole orchestrator. When I prompted Claude Code to implement `run_agent`, I could point at that paragraph and get correct branching on the first try.

**Where the implementation diverged:** My spec said "extract parameters from the user message" without committing to a method. During coding I had to pick between regex and an LLM call. I went with regex because it's faster and deterministic, but I should have locked that decision into the spec earlier. Lesson: a spec only works if it decides the hard questions, not just the obvious ones.

---

## AI usage

Used Claude Code in VS Code throughout the project. Two specific moments:

**1. Implementing `search_listings`**

I pasted my Tool 1 block from planning.md (inputs, return shape, failure mode) and told Claude Code to use `load_listings()` from the data loader.

It produced a working implementation but stuffed everything into one big list comprehension. I asked it to break it into named steps because the dense version was harder to read. The logic was right, the readability needed work.

**2. Implementing the planning loop in `agent.py`**

I gave Claude Code the Planning Loop section, the State Management section, and the architecture diagram. I specifically said to use regex (not an LLM) for query parsing and to guard the early-exit case.

First version of the regex only matched "under $30" exactly. I had it expand to also catch "less than $30", "$30 or less", and "under 30". I also pushed back on a `try/except` it wrapped around the whole loop — I wanted exceptions to surface during development, not get silently swallowed.

---

## How to run

```bash
git clone https://github.com/eriicsalim77/FitFindrAgent.git
cd FitFindrAgent

python -m venv .venv
.venv\Scripts\activate              # Windows
# source .venv/bin/activate         # Mac/Linux

pip install -r requirements.txt

copy .env.example .env
# Open .env, add your Groq API key

python app.py
```

Open the URL printed in your terminal (usually http://127.0.0.1:7860).

## Run the tests

```bash
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

11 tests covering all three tools and their failure modes. All passing.

---

## Repo

https://github.com/eriicsalim77/FitFindrAgent