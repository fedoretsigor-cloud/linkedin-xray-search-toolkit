# Session Context - Search Step Back - 2026-05-12

## Current State

We paused because the search planner became too implicit and confusing for the user.

The user no longer feels in control of the search:

- `Role Signals` look editable, but in semantic family mode they mostly select/confirm a family and affect `Title Focus`; they do not directly change `Evidence Core`.
- `Tech Stacks` were being re-bucketed by `search_intent` into language/tooling groups, so the query sent to providers did not always match what the user typed.
- `family`, `brief`, `search_intent`, `adaptive waves`, and default query groups created hidden behavior.
- The user wants to step back and rebuild the planner with a clear contract and TDD, not continue adding patch-on-patch optimizations.

Do not continue with broad hidden planner optimizations until the query contract is simplified and tested.

## Important Product Direction

The desired mental model should be:

- `Detected Role` is the main role anchor.
- `Role Signals` are user-controlled role/title signals and should visibly affect generated queries, or the UI label/help text must change.
- `Tech Stacks` are user-controlled evidence/boost terms. One line is one group. Separators `|`, `,`, and `;` should behave predictably.
- `Location` is a required location anchor and later a strict validation/scoring signal.
- `Search Depth` should mainly control provider/page depth, not hidden semantic rewrites.
- `Brief` should prefill the form only. Once the user edits fields, hidden brief/search_intent logic should not override what the user sees.
- `Family` can be a visible helper/preset, but should not silently override query construction.
- `Preview Queries` must be the source of truth: the same queries shown in the UI are the same queries sent to providers.

## Current Architectural Recommendation

Do not restart the whole repo from zero. Restart the search planner contract as `Search Engine v2`.

Suggested simple pipeline:

1. `SearchBrief`
2. `SearchFormState`
3. `SearchPlan`
4. `ProviderCalls`
5. `RawResults`
6. `CandidateEvidence`
7. `RankedCandidates`
8. `SearchReport`

Core principle:

- Query planning is for discovery.
- Scoring/ranking is for precision.
- Stack/domain terms should usually be evidence/boost, not always mandatory filters.

Suggested stack strategy:

- Wave 1: role + location discovery, stack not mandatory.
- Wave 2: role + stack + location evidence.
- Scoring: stack match boosts; missing stack lowers score but should not immediately reject unless strict mode is chosen.

Potential UI option later:

- `Tech Stack mode: Boost match / Must-have / Ignore`

## Recent Concrete Findings

### Tavily Timeout

Observed error:

```text
tavily API error: Network error: ReadTimeout
```

Root cause:

- Standard uses only Tavily.
- If Tavily times out, there is no fallback provider.

Implemented local improvement:

- `src/tavily_client.py` now retries transient Tavily timeout/network failures.
- Timeout increased to `45s`.
- Up to 3 attempts total.
- `src/search_orchestrator.py` now classifies network/timeout errors and shows a more useful message.

### Query Text Was Cut Off

Technical reports were hiding full queries with CSS ellipsis.

Implemented local improvement:

- `static/styles.css` now wraps `.query-group-sample` instead of truncating it.

### Java Backend Default Simplification

User wanted Java Backend default stack to be simple:

```text
Java | Spring
```

Local changes:

- `static/role_presets.js`
- `templates/index.html`
- `static/app.js`
- `src/query_group_expander.py`

### Standard Default

User wanted UI default Search Depth to be `Standard`.

Local changes:

- `templates/index.html`
- `static/app.js`

### Tech Stack Re-Bucketing Bug

Observed confusing behavior:

```text
Java | Spring | AWS | Kafka
```

was transformed into:

```text
Java
Spring | AWS | Kafka
Java | Spring
```

This created 6 Tavily calls and hidden queries that did not match the user's mental model.

Implemented local improvement:

- `src/web_search.py` now treats manual `Tech Stacks` as the source of truth.
- `static/app.js` preview now also preserves manual grouping.
- Terms are chunked by 3 only for query-length safety.

Expected examples after the local change:

```text
Java | Spring
=> 2 Standard calls

Java | Spring | AWS
=> 2 Standard calls

Java | Spring | AWS | Kafka
=> 4 Standard calls
```

## Current Confusion To Resolve Before More Coding

The biggest unresolved UX/product issue:

`Role Signals` currently feel fake because they do not directly affect `Evidence Core` when a semantic family is matched.

Current behavior for Java Backend:

```text
Detected Role: Java Backend Developer
Role Signals: Java Developer, Backend Engineer
Tech Stack: Java | AWS
Location: Ukraine
```

Evidence Core is generated from semantic family terms:

```text
site:linkedin.com/in/ "Java" ("Backend" OR "Back End" OR "Engineer" OR "Developer" OR "Software Engineer") "Java" "Ukraine"
site:linkedin.com/in/ "Java" ("Backend" OR "Back End" OR "Engineer" OR "Developer" OR "Software Engineer") "AWS" "Ukraine"
```

So `Java Developer` and `Backend Engineer` do not appear directly in Evidence Core. They mainly influence family selection and Title Focus.

This is likely wrong for UX.

## Proposed Next Step

Stop patching the current planner.

Next work should be a TDD query planner reset:

1. Write a one-page query contract.
2. Add golden tests for query generation.
3. Implement a small deterministic planner that makes UI inputs directly visible in generated provider calls.
4. Only then reintroduce family helpers as explicit, visible presets.

Suggested first golden tests:

1. Java Backend, role signals `Java Developer`, `Backend Engineer`, stack `Java | Spring`, location `Ukraine`, Standard.
2. Java Backend, stack `Java | Spring | AWS | Kafka`, Standard.
3. Energy / ETRM Business Analyst, Houston, Standard.
4. Same Energy search with `Role Signals` changed, proving generated queries change.
5. Stack mode `Boost` vs `Must-have`, if introduced.

## Current Working Tree Note

There are local uncommitted changes. The user did not ask to commit.

Known modified areas:

- `src/query_group_expander.py`
- `src/search_orchestrator.py`
- `src/tavily_client.py`
- `src/web_search.py`
- `static/app.js`
- `static/role_presets.js`
- `static/styles.css`
- `templates/index.html`

There is also local `server.log`; do not commit logs unless intentionally needed.

## Server

Local server was restarted and was responding at:

```text
http://127.0.0.1:5000
```

