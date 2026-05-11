# Product Roadmap: AI-Assisted Sourcing Workflow

## Business Goal

Build a sourcing workflow system that helps a human recruiter move from an official hiring requirement to a verified candidate decision.

The product should not behave like a bot that logs into LinkedIn or scrapes private pages. It should combine public search, human-in-the-loop verification, AI analysis, and candidate tracking.

## Target Workflow

1. A human provides a link to an official portal or public page with hiring requirements.
2. The system opens the accessible public page and extracts the hiring requirement.
3. The AI agent decides who we are looking for and creates a structured search brief.
4. The system explains its understanding to the human.
5. The human confirms, corrects, or adds feedback.
6. The system builds search queries and runs public source search.
7. The human reviews search results.
8. The human manually opens selected profiles and pastes profile text into the system.
9. The system analyzes the pasted profile and decides whether the candidate fits.
10. The system suggests what to ask or clarify with the candidate.
11. The system drafts a candidate message.
12. After communication, the human may receive a resume.
13. The human uploads the resume, optionally after removing personal data.
14. The system analyzes the resume against the requirement and previous profile analysis.
15. The system updates the candidate decision and next action.
16. Once a human starts working on a candidate, the system tracks communication and workflow state.
17. Later, the same workflow can be controlled through a conversational agent interface, where the human talks to the system like a live sourcing copilot.

## AI Agent Role

The product needs an AI workflow agent, not a fully autonomous browser bot.

The agent should:

- Read public hiring requirements from official portals.
- Extract role, seniority, location, domain, must-have skills, nice-to-have skills, exclusions, and open questions.
- Create a structured search brief.
- Explain the brief to the human before search starts.
- Accept human feedback and revise the search brief.
- Generate search strategy, role variants, stack variants, and source strategy.
- Analyze pasted profile text.
- Analyze uploaded resumes.
- Compare profile and resume evidence against the requirement.
- Produce fit decisions, risks, missing evidence, clarifying questions, and outreach drafts.
- Track candidate workflow state.
- Eventually communicate with the human through a chat layer that can explain, revise, and trigger the same workflow actions.

The agent should not:

- Automatically use a human's logged-in LinkedIn session.
- Use LinkedIn cookies or browser automation to scrape profiles.
- Mass-open profiles as a bot.
- Extract private or login-gated data.
- Send messages to candidates without human approval.
- Hide important state changes inside chat without showing what changed in the structured workflow.

## Product Phases

### Phase 1: Requirement Intake

Status: Done in MVP.

Add a requirement URL input.

The system fetches accessible public content from the URL and extracts:

- Role title.
- Seniority.
- Location and remote constraints.
- Must-have skills.
- Nice-to-have skills.
- Domain context.
- Employment type.
- Exclusions or disqualifiers.
- Ambiguities and missing information.

Output: structured requirement brief.

Current implementation:

- Added Requirement Intake UI block.
- Added public URL fetcher.
- Added OpenAI-powered requirement extraction.
- Added structured requirement brief output.
- Added `OPENAI_API_KEY` / `OPENAI_MODEL` configuration.
- Added "Apply to Search Builder" action.

### Phase 2: Human Confirmation

Status: Done in MVP, with future revision flow still planned.

Before running search, show:

- "I understood the task this way."
- Search target.
- Must-have criteria.
- Nice-to-have criteria.
- Suggested role variants.
- Suggested stack keywords.
- Suggested locations.
- Open questions.

Search should start only after human confirmation or correction.

Current implementation:

- The system shows an "Agent understanding" card.
- The human can review the extracted brief before applying it.
- Search Builder now starts with an explicit search mode: `Manual search` or `From vacancy URL`.
- Manual search can build the same Search Brief / Search Strategy Preview without a vacancy URL.
- Applying the brief fills the existing Search Builder.
- The human can manually edit Role, Role Variants, Tech Stacks, Locations, Sources, and Results Limit.
- Running search automatically saves `confirmed_brief` from the current form fields.
- Manual searches now also save `confirmed_brief` with `source_type = manual`.
- The run and sourcing project retain both the original extracted brief and the confirmed brief.

Remaining work:

- Add a true revision flow later: human feedback -> revised structured brief.
- Add clearer UI grouping so the left panel does not become too heavy.
- Continue polishing the compact Search Brief UI based on real owner testing.

### Phase 3: Search Strategy Agent

Status: Done in MVP, with explainability improvements remaining.

Generate a search plan from the confirmed brief:

- Role variants.
- Stack variants.
- Source selection.
- Query count.
- Query examples.
- Recall vs precision tradeoff.

The system should explain why it chose the queries.

Current implementation:

- Added search strategy compression.
- Long requirement briefs are converted into Tavily-friendly query chunks.
- Skills are split into compact query groups.
- Query length is kept under Tavily limits.
- Tavily errors now return readable JSON messages.
- Search strategy preview is shown before search for both manual and vacancy-assisted searches.
- Role is no longer intended to be treated only as a required title term. The next planner iteration should use evidence-first query waves: function evidence, tool/vendor evidence, domain evidence, and location evidence, with title-focused queries kept as a smaller precision lane.
- Search strategy preview now uses "planned searches" language instead of unclear "base queries".
- `Remote + Country/City` inputs are reduced to the concrete country/city in outgoing search queries, while strict location filtering remains active.
- Generic Tavily boosters such as `profile`, `resume`, `cv`, `frontend`, and `candidate` were removed because they narrowed or polluted searches.
- For large result limits, search now expands through role-family query groups instead of repeating generic boosters.
- For example, Java Backend at 200 candidates can expand into groups such as Java/JVM, Spring, Kafka/RabbitMQ, AWS/cloud, microservices, databases, REST/API, Docker/Kubernetes, Hibernate/JPA, and CI/CD.
- Added the first semantic role pattern layer for common IT role families, starting with QA Automation, Java Backend, Frontend, Fullstack, iOS, Android, DevOps/SRE, Data, ML/AI, and Embedded.
- Semantic role family selection now uses role/title signals plus extracted requirement/search-intent context.
- Added an Energy / ETRM Business Analyst semantic family for Front Office, Power Trading, Energy Trading, ETRM/CTRM, Orchestrade, Endur, Openlink, RightAngle, and Allegro signals.
- Energy / ETRM searches now use grouped-anchor query variants instead of one oversized Boolean query. Example pattern: `"Business Analyst" "Front Office" "Power Trading" "Endur" "houston"`.
- City/country inputs now search the primary city token, for example `Houston, United States` -> `"houston"`, while strict location validation still uses the full displayed location.
- Search Strategy Preview now includes search depth, provider list, base query count, provider-pass count, and sample provider queries.
- Search Depth UI added: Standard, Medium, Extended, and Max.
- Max search depth now uses deeper API pagination for paginated providers: up to 10 pages for Bing / SerpApi, Google / SerpApi, and Google / Serper.
- Adaptive search waves are implemented for 100/200-candidate searches. Next iteration: Standard, Medium, and Extended should run Evidence Core followed by a small Title Focus precision wave. Max should run Evidence Core, then Title Focus, then Evidence Expansion only if the requested candidate target has not been reached.
- Dynamic adaptive-wave reranking is implemented as a first intelligence layer: when search reaches later waves, the remaining query plan is reordered using completed-wave query-group unique lift and provider lift.
- Max stopping policy should be explicit and budget-safe: stop when `accepted_candidates >= selected_result_limit`, or when `executed_calls >= planned_call_cap`, or when all planned waves/pages are exhausted. Max must not run open-ended searches.
- Role presets now cover more non-developer sourcing cases: Business Analysis, Data / BI Analytics, Product / Project Management, Architecture / Leadership, and UX / Product Design. These groups also have backend/frontend semantic families and query groups, not only dropdown labels.
- The run stores `search_strategy`.
- The sourcing project stores the latest `search_strategy`.

Remaining work:

- Explain recall vs precision tradeoffs.
- Allow the human to approve or edit query groups before running search.
- Add provider-level explainability: raw results, strict-location filtered results, deduped contribution, and unique candidate lift per provider.
- Tune the conservative adaptive replacement layer on real searches: weak early signals can replace low-ranked later groups with semantic-family alternates, but groups are not skipped outright.
- Implement the evidence-first query planner: Evidence Core should become the default first wave, Title Focus should become a smaller second precision wave, and Evidence Expansion should be reserved for Max or explicit high-recall runs.
- Improve query planner clarity further after testing real searches.

### Phase 4: Candidate Search

Status: Done in MVP with sourcing project persistence.

Run public source search using the existing search pipeline.

Save each search as a sourcing project or search run:

- Requirement brief.
- Confirmed search strategy.
- Queries used.
- Candidates found.
- Search source evidence.

Current implementation:

- Tavily public search is wired into the app.
- Search results are normalized, deduped, scored, and saved as search runs.
- Hybrid provider orchestration is now supported. A run can execute the same query set across multiple search providers and dedupe the combined results.
- Supported provider plumbing now includes Tavily, Bing via SerpApi, Google via SerpApi, and Google via Serper.
- Search depth controls provider selection: Standard = Tavily; Medium = Tavily + Bing / SerpApi; Extended = Tavily + Bing / SerpApi + Google / SerpApi; Max = Tavily + Bing / SerpApi + Google / SerpApi + Google / Serper.
- Max intentionally keeps the user-facing provider set focused on Tavily, Bing / SerpApi, Google / SerpApi, and Google / Serper. Experimental or noisy providers are kept out of the main UI until they prove useful in benchmarks.
- Deep-result pagination is implemented through provider APIs, not browser automation. For 200-candidate Max searches, the planner can schedule up to 10 pages for each paginated provider.
- Provider failures inside a multi-provider run are captured as provider warnings instead of failing the whole search when another provider can still return results.
- Candidate records now retain the search provider that found them, so the UI can show where a profile came from.
- Candidate table Role and Stack now display profile evidence extracted from indexed title/snippet text, not the original search request. Query role/stack context is preserved separately in candidate details for audit.
- `.env.example` documents `SERPAPI_API_KEY`, `SERPER_API_KEY`, `TAVILY_API_KEY`, `SEARCH_MAX_EXECUTED_CALL_CAP`, location verification settings, and OpenAI settings.
- Provider diagnostics are stored in `search_strategy.result_diagnostics` for analysis, including raw rows, quality rows, accepted rows, strict-location rejects, verification attempts, and provider breakdowns.
- Detailed diagnostics are hidden from the main results UI by default so the recruiter sees a cleaner candidate table, while the run JSON remains auditable.
- Added recruiter-friendly Search Explanation UX after each run. It summarizes what was searched, candidate fill, elapsed time, executed vs planned provider calls, strict-location filtering, top contributing providers, top query groups, and adaptive-wave behavior.
- Technical provider/query-group/adaptive/benchmark reports remain available, but are collapsed behind `Technical reports` so the main UI reads like a sourcing summary rather than a debug dashboard.
- A compact Provider Contribution Report is now shown after each search and can be exported to CSV. It summarizes raw rows, strict-location rejects, accepted rows, final unique candidates, dedupe/cap loss, executed calls, and warnings per provider.
- Adaptive wave diagnostics are stored in `search_strategy.adaptive_waves` and shown inside the contribution report, including which waves ran, calls per wave, raw rows, accepted rows, and unique candidates after each wave.
- Dynamic wave selection is stored in `search_strategy.adaptive_waves.dynamic_selection` and shown in the adaptive-wave report. The first slice reranks remaining Wave 2/3 calls using Wave 1 productive/weak query groups and provider lift.
- The second adaptive-intelligence slice is implemented as conservative replace-only logic. When completed waves show weak groups, low-ranked later groups can be replaced by unused alternates from the same semantic family; the system records `replacement_groups` in `dynamic_selection` and does not skip groups outright.
- Energy / ETRM Business Analyst now has grouped-anchor alternates such as CTRM / commodity trading, Middle Office / risk management, trading systems / Endur, trade capture / energy trading, RightAngle / Allegro, Openlink / commodity risk, natural gas / power trading, crude oil / refined products, scheduling / settlements, and commodity risk / energy risk.
- Gap analysis from manually reviewed Houston Front Office / ETRM candidates showed that title-first search missed strong profiles whose public evidence used `Consultant`, `SME`, `Lead`, `Architect`, `Developer`, `Support Engineer`, `Trading Systems`, `Trade Capture`, `OpenLink`, `RightAngle`, or `Allegro` instead of exact `Business Analyst` + `Front Office`. Planned fix: move from title-first to evidence-first planning.
- Planned wave model: Evidence Core = high-precision role/function + tool/domain + strict location; Title Focus = narrow exact-title precision lane; Evidence Expansion = consultant/SME/lead/architect/developer/support-engineer + tool/domain + strict location, enabled in Max only when still below target.
- Standard, Medium, and Extended now include Evidence Core and Title Focus. Max includes Evidence Core, Title Focus, and Evidence Expansion, with early stop at selected result limit or planned call cap.
- Max runs now keep a budgeted provider-call cap separate from the full page/depth plan. Search stops explicitly at target reached, call cap reached, or plan exhausted, and stores the stop reason in `search_strategy`.
- Evidence Expansion now has an audit summary in `search_strategy.adaptive_waves.evidence_expansion`, so Technical reports show whether the high-recall wave ran, partially ran, or was skipped because target/cap stopped the run.
- Query-group contribution diagnostics are stored in `search_strategy.query_group_contribution_report` and shown inside the contribution report, including calls, raw rows, accepted rows, final unique candidates, dedupe/cap loss, sample query, and provider lift by group.
- Search runs store the actual executed provider queries, including page/start/first offsets, so we can audit what was sent after early stopping.
- Hybrid role presets and editable role variants are implemented.
- Query expansion now prefers meaningful family-specific search angles over repeated identical queries or noisy generic boosters.
- Devpost-specific normalization now avoids treating project titles as candidate names.
- Added `project_id`.
- Added `data/projects/{project_id}.json`.
- Added `data/sourcing_projects.json`.
- Added `/api/projects` and `/api/projects/<project_id>`.
- Search runs are linked to sourcing projects.
- Repeated searches can attach to the same sourcing project.

Remaining work:

- Improve source-specific search behavior per source.
- Benchmark provider quality across Standard, Medium, Extended, and Max search depths.
- Add a short "why not filled" explanation when final candidates are below the requested limit, for example Standard depth only used Tavily, strict location removed many rows, or too few query groups produced unique lift.
- Add next-action suggestions in the Search Explanation card, for example try Extended/Max depth, broaden role signals, or add another location only when the diagnostics support that advice.
- Use the new query-group contribution report in real benchmark runs and tune group ordering/selection.
- Benchmark the new evidence-first wave split on 100/200-candidate searches: Evidence Core first, Title Focus second, Evidence Expansion only in Max if the target is not filled.
- Tune the second adaptive-wave replacement layer on real 100/200-candidate searches so replacements improve unique lift without reducing recall.
- Add a Projects UI so users can browse projects directly, not only search history.
- Decide whether Render production should use persistent disk/database instead of local JSON for long-term storage.

### Phase 5: Manual Profile Review

Status: In progress, first vertical slice implemented.

Add a manual review area for each candidate:

- "Open source profile" link.
- "Paste profile text" textarea.
- "Analyze pasted profile" action.

The human opens LinkedIn or another source manually, copies relevant profile text, and pastes it into the system.

The system analyzes:

- Role fit.
- Seniority evidence.
- Stack evidence.
- Domain evidence.
- Location evidence.
- Availability signals.
- Risks and missing evidence.
- Questions to ask the candidate.
- Revised fit score.
- Suggested outreach message.

Current implementation:

- Added Manual Profile Review block to the selected candidate panel.
- Human can paste profile text manually.
- Added profile review endpoint under the sourcing project.
- Added OpenAI-powered profile review agent.
- Review is saved into `candidate_reviews` on the sourcing project.
- UI shows decision, score, evidence, risks, questions to ask, and outreach draft.

Remaining work:

- Improve UI layout so profile review does not make the right panel too heavy.
- Show previously saved reviews when loading historical runs/projects.
- Show saved candidate reviews when loading historical runs/projects.
- Prepare the review data for resume review and decision memory.

### Phase 6: Resume Review

Status: First slice in progress.

First slice now supports:

- PDF/DOCX resume upload.
- Text fallback when upload extraction is not available or the user wants to paste sanitized text.
- Resume analysis against the confirmed brief, candidate result, and latest profile review.
- Resume review persistence under the sourcing project.
- Saved resume reviews load back into the candidate panel.

The human may remove personal data before uploading.

The system compares the resume against:

- Original requirement brief.
- Confirmed search strategy.
- Profile analysis.
- Profile review analysis.
- Candidate clarification notes when available later.

Output:

- Fit decision.
- Evidence table.
- Missing evidence.
- Contradictions between profile and resume.
- Clarifying questions.
- Recommended next action.

Remaining work:

- Polish the right-panel layout so profile review and resume review do not feel too heavy.
- Add a clearer reviewed/resume-reviewed indicator in the candidate table.

### Phase 7: Decision Memory

Status: Not started.

Store a complete candidate decision trail:

- Why this candidate was selected.
- What evidence supported the fit.
- What risks were found.
- What questions were asked.
- What the candidate answered.
- What the resume confirmed or contradicted.
- Final recommendation.

This makes the system useful as a sourcing memory layer, not just a search interface.

### Phase 8: Conversational Sourcing Copilot

Status: Planned for later.

Add a chat layer on top of the structured workflow.

The chat should not replace the reliable workflow screens at first. It should call the same backend actions that already exist:

- Analyze requirement URL.
- Explain extracted requirement brief.
- Ask human confirmation questions.
- Revise the brief based on feedback.
- Build search strategy.
- Explain query tradeoffs.
- Run search after confirmation.
- Summarize candidate results.
- Explain why a candidate looks strong or weak.
- Draft candidate outreach.
- Update candidate status.
- Prepare next action reminders.

Example interaction:

```text
Human: Here is the vacancy link.
Agent: I understood the role as Senior Java Backend Engineer for low-latency trading systems. I have 3 questions before search.
Human: Location is EU only, low latency is mandatory, Spring is nice-to-have.
Agent: Updated. I will search for Java Backend Engineer, Low Latency Java Developer, Trading Systems Engineer. Ready to run?
Human: Run it.
Agent: Found 40 candidates. 8 have explicit latency/trading evidence. Want to review those first?
```

The conversational layer needs project memory:

- Current requirement brief.
- Confirmed search strategy.
- Last search run.
- Candidate list.
- Selected candidate.
- Candidate status.
- Profile analysis.
- Resume analysis.
- Communication notes.

Implementation guidance:

- Build reliable workflow actions first.
- Add chat only after actions are stable.
- Chat messages should never be the only source of truth.
- Every agent action should update structured project state.
- Risky actions should ask for human confirmation.
- The user should always see what changed after the agent acts.

### Phase 9: Candidate Communication Tracker

Status: Backlog, intentionally moved to the end.

This is valuable, but less critical than profile review, resume review, and decision memory.

Once the core review workflow is stable, create a candidate workflow record.

Suggested statuses:

- Found.
- Profile reviewed.
- Needs clarification.
- Message drafted.
- Contacted.
- Replied.
- Waiting for resume.
- Resume received.
- Resume reviewed.
- Shortlisted.
- Rejected.
- On hold.

Track:

- Last action.
- Next action.
- Communication notes.
- Candidate questions.
- Candidate answers.
- Resume availability.
- Decision history.

## Suggested Data Model

### Sourcing Project

- `id`
- `requirement_url`
- `requirement_raw_text`
- `requirement_brief`
- `confirmed_brief`
- `search_strategy`
- `created_at`
- `updated_at`

### Candidate

- `id`
- `project_id`
- `name`
- `source`
- `source_url`
- `search_query`
- `initial_score`
- `current_score`
- `status`
- `created_at`
- `updated_at`

### Candidate Review

- `candidate_id`
- `pasted_profile_text`
- `profile_analysis`
- `resume_text`
- `resume_analysis`
- `questions_to_ask`
- `outreach_message`
- `decision`
- `risks`
- `next_action`

### Communication Event

- `candidate_id`
- `event_type`
- `notes`
- `created_at`

### Agent Conversation

- `id`
- `project_id`
- `messages`
- `active_context`
- `last_agent_action`
- `created_at`
- `updated_at`

### Agent Action

- `conversation_id`
- `action_type`
- `input`
- `output`
- `requires_confirmation`
- `confirmed_by_human`
- `created_at`

## Compliance And Safety Boundaries

The safe architecture is:

```text
Public requirement URL
-> AI requirement extraction
-> human confirmation
-> optional conversational clarification
-> public search
-> human manually opens profiles
-> human pastes profile text
-> AI analysis
-> human-controlled communication
-> resume upload
-> AI review
-> candidate tracking
```

Avoid:

```text
Logged-in LinkedIn automation
-> profile scraping
-> automated messaging
-> private data extraction
```

## Next Implementation Steps

Recommended next build order:

1. Done: Add a `docs/` roadmap and keep this plan as the product source of truth.
2. Done: Add requirement URL intake and public page fetch.
3. Done: Add requirement brief extraction.
4. Done in MVP: Link extracted brief to the existing search builder.
5. Done in MVP: Save confirmed brief from current fields at search time.
6. Done in MVP: Add compact search strategy generation for Tavily.
7. Done in MVP: Store confirmed brief and generated query plan with each search run.
8. Done in MVP: Add sourcing project persistence and project-linked search runs.
9. Done first slice: Add manual profile review textarea and profile analysis.
10. Done first slice: Save candidate reviews under the sourcing project.
11. Done first slice: Load saved candidate reviews when opening historical runs/projects.
12. In progress: Add PDF/DOCX resume upload and resume analysis.
13. Done first slice: Improve search engine recall for large result limits using semantic family query groups.
14. Done first slice: Add hybrid provider search with depth controls for Tavily, Bing / SerpApi, Google / SerpApi, and Serper.
15. Done first slice: Add provider error handling so missing credits, auth failures, and rate limits surface as provider warnings without killing multi-provider runs.
16. Done first slice: Add strict country-level LinkedIn subdomain proof for country searches, while keeping city searches strict on city evidence.
17. Done first slice: Increase Max depth API pagination to 10 pages for paginated providers.
18. Done first slice: Store provider diagnostics and executed-query audit trails while hiding the noisy diagnostics block from the main UI.
19. Done first slice: Add provider contribution reporting for raw, filtered, deduped, and unique-lift counts with CSV export.
20. Done first slice: Add adaptive second/third search waves when a 100/200-candidate search returns too few unique results.
21. Done first slice: Expand role presets and semantic query families beyond engineering into analysts, managers, architects, and product/design roles.
22. Done first slice: Add query-group contribution reporting with unique lift, accepted rows, provider lift, and CSV export.
23. Done first slice: Use Wave 1 query-group unique lift and provider lift to rerank the remaining adaptive wave plan.
24. Done first slice: Let adaptive waves replace weak groups with semantic-family alternates, without aggressive skip logic.
25. Planned next: Replace title-first wave planning with evidence-first planning. Standard/Medium/Extended should run Evidence Core then Title Focus. Max should add Evidence Expansion only until target or planned call cap.
26. Later: Add decision memory across profile and resume review.
27. Later: Add conversational sourcing copilot on top of stable workflow actions.
28. Backlog: Add candidate communication tracking after the core review workflow is stable.

## Current Decision

The idea is strong and should be pursued as a staged product.

The immediate next architectural direction is to evolve the current search app into a human-in-the-loop AI sourcing workflow, while keeping LinkedIn interaction manual and safe.

The conversational agent idea is valuable and should remain in the roadmap. It should be implemented as a later interface layer over stable workflow actions, not as an early replacement for structured screens.

Owner search-engine questions are tracked in `docs/questions-from-owner.md` under the marker "Questions from owner". Use that file as the working discussion log before promoting decisions into this roadmap.

## Progress Snapshot

Last updated: 2026-05-11.

Completed:

- Roadmap document created.
- Tavily client extracted.
- Tavily query builder extracted.
- Search pipeline orchestrator added.
- Dedupe, scoring, enrichment, and Devpost normalization improved.
- Hybrid role preset Search Builder added.
- Requirement Intake Agent added.
- OpenAI API integration added.
- Public requirement URL fetcher added.
- Requirement brief extraction added.
- Apply brief to Search Builder added.
- Tavily query compression added to prevent query length errors.
- Search strategy preview added.
- Requirement Brief main UI simplified into compact bullets.
- Role variants are now searched as OR alternatives after the required main role term, instead of multiplying separate title queries.
- Semantic role patterns now convert recognized literal titles into broader searchable patterns, for example QA Automation -> `"Automation" ("Engineer" OR "QA" OR "Tester" OR "SDET")`.
- Semantic family detection now considers extracted requirement context, not only Role and Role Variants.
- Search Builder now labels role fields as Detected Role and Role Signals, and manual edits immediately refresh the strategy preview.
- Added an explicit Update Strategy Preview action for manual search-builder changes.
- Manual role/signal matches now override older extracted requirement context in semantic family selection, with inline family/pattern feedback under the update button.
- Added explicit `Search mode` selection: Manual search or From vacancy URL.
- Added a persistent Search Brief / Search Strategy Preview card that works for manual searches without a vacancy URL.
- Manual searches now save a confirmed brief and can create sourcing projects without crashing when no requirement brief exists.
- Search Strategy Preview now uses a compact summary plus expandable detail sections.
- Search Strategy Preview now explains role logic, strict location, planned searches, and result-limit behavior.
- Remote plus concrete location now searches the concrete location instead of the literal remote phrase.
- Remote plus concrete location now removes standalone `remote` even when it is split by punctuation, for example `Remote, Brazil` -> `Brazil`.
- Requirement Brief now shows compact canonical search-anchor chips and hides long extracted text in expandable sections.
- Requirement Brief now also hides suggested role variants and open questions in expandable sections.
- Confirmed brief is saved automatically from current fields at search time.
- Search Intent Builder added so long human requirements become concise searchable anchors.
- Strict location policy started: location now requires indexed evidence, not only query context.
- Generic Tavily boosters removed.
- Large-result search now expands through semantic role-family query groups instead of `profile/resume/cv/frontend` booster variants.
- Search progress active-wait UX improved for long-running searches.
- Sourcing project persistence added.
- Search runs are linked to sourcing projects.
- Project API added.
- Saved candidate reviews load back into the UI.
- Resume review backend, file extraction, and first UI added.
- Saved resume reviews load back into the UI.
- Energy / ETRM Business Analyst role family added with grouped Front Office, Power Trading, Energy Trading, ETRM, Orchestrade, and Endur query anchors.
- Grouped family search now sends smaller, higher-recall queries instead of one oversized Boolean expression.
- Hybrid search orchestration now supports multiple providers in one run and dedupes across providers.
- Bing / SerpApi and Google / SerpApi were added as first hybrid search providers.
- Google / Serper was added as a prepared fourth provider with `SERPER_API_KEY` configuration.
- Search Depth UI added with Standard, Medium, Extended, and Max provider presets.
- Max search depth now paginates up to 10 API pages for Bing / SerpApi, Google / SerpApi, and Google / Serper.
- Max provider set is currently focused on Tavily, Bing / SerpApi, Google / SerpApi, and Google / Serper.
- Experimental provider options that did not yet prove useful are hidden from the main Search Depth UI.
- Search Strategy Preview now shows provider list, base query count, provider-pass count, and provider-tagged sample queries.
- Candidate detail UI now shows which search provider found the candidate.
- Candidate table Role/Stack now show what was actually found in the indexed profile evidence, with `N/A` when no role/stack evidence is extractable; matched query context remains visible in details.
- Multi-provider search now records provider warnings without failing the whole run when other providers succeed.
- Provider warning classification now distinguishes credits/quota, rate limit, auth/access, missing configuration, and generic API errors.
- Strict location filtering now treats query text alone as insufficient evidence.
- Country-only searches can use LinkedIn country subdomains as local proof, for example `pl.linkedin.com` for Poland, while city searches still require city evidence from indexed profile/header/snippet text.
- Provider diagnostics are stored in run JSON but hidden from the main UI.
- Provider Contribution Report now surfaces compact per-provider raw rows, strict-location rejects, accepted rows, final unique candidates, dedupe/cap loss, executed calls, and CSV export.
- Query Group Contribution Report now surfaces per-group calls, raw rows, accepted rows, final unique lift, dedupe/cap loss, provider lift, sample query, and CSV export.
- Adaptive search waves now run for 100/200-candidate searches and record per-wave diagnostics.
- Adaptive waves now rerank the remaining Wave 2/3 plan at later wave boundaries when completed waves have enough signal, using productive/weak query groups and provider lift.
- Adaptive waves now have a conservative replace-only layer: weak completed-wave signals can swap low-ranked later query groups for unused semantic-family alternates, with replacement audit shown in Technical reports.
- Energy / ETRM grouped-anchor searches now expose unique query-group labels and alternate grouped anchors for replacement tuning.
- Added manual gap-analysis docs for Houston Front Office / ETRM searches:
  - `docs/photo-only-gap-analysis-front-office-power-ba.md`
  - `docs/top30-photo-only-evidence-pattern-analysis.md`
- Product decision: move the query planner toward evidence-first waves. Standard/Medium/Extended should run Evidence Core plus Title Focus. Max should run Evidence Core, Title Focus, and Evidence Expansion, stopping at selected target, planned call cap, or exhausted plan.
- Evidence-first implementation step 1 completed: query groups, executed queries, adaptive wave summaries, candidate details, and query-group reports now carry explicit `wave_type` / `wave_type_label` metadata. Current legacy queries are correctly labeled as `title_focus` until Evidence Core and Evidence Expansion query generation is added.
- Evidence-first implementation step 2 completed: Energy / ETRM grouped-anchor searches now have explicit Evidence Core and Evidence Expansion query groups for BA/function evidence, vendor/tool evidence, domain evidence, and consultant/SME/lead/developer evidence. The backend can generate these waves via `query_wave_types` without changing default search-depth behavior until the mapping step lands.
- Evidence-first implementation step 3 completed: Search Depth now maps Energy / ETRM grouped-anchor searches to evidence-first waves. Standard, Medium, and Extended plan Evidence Core then Title Focus. Max plans Evidence Core, Title Focus, then Evidence Expansion, with later waves naturally skipped once the selected result target is filled.
- Product decision: evidence-first should become a general pattern for every Role Group, not only Energy / ETRM. Each role family should eventually have generic Evidence Core, Title Focus, and Evidence Expansion groups built from role/function evidence, stack/tool evidence, domain evidence, and strict location. Energy / ETRM is the first specialized evidence pattern; similar specialized patterns should be added to other role families as domain knowledge is supplied by the owner.
- Evidence-first implementation step 4 completed: non-Energy semantic Role Groups now use a generic evidence builder. Generic Evidence Core combines family core terms, family role/function terms, active stack/tool groups, and strict location; generic Title Focus uses exact user-provided titles/variants plus stack/tool groups; generic Evidence Expansion uses broader role/function alternates plus alternate stack groups. Energy / ETRM remains the first specialized evidence pattern.
- Evidence-first implementation step 5 completed: Max runs now stop explicitly at selected target, planned call cap, or exhausted plan. The backend stores `stop_reason`, `planned_call_cap`, `budgeted_query_count`, `executed_search_query_count`, and separate verification query counts.
- Evidence-first reporting step completed: Search Explanation and Technical reports now show budgeted vs full planned provider calls, stop reason, adaptive wave statuses, and whether Evidence Expansion ran, partially ran, or was skipped.
- Evidence-first local verification completed: Python compile checks and frontend syntax checks pass after the wave model, generic evidence builder, Max call-cap, and report updates.
- Captured first large-search timing benchmark: Data Analyst, Poland, Max depth, 200 candidates completed in 996.55 seconds, about 16 minutes 37 seconds, with 203 executed provider queries out of 372 planned.
- Search progress now shows elapsed time, approximate remaining time, and a more realistic large-search estimate instead of sitting silently at 87%.
- Captured second large-search benchmark: QA Automation Engineer, Poland, Max depth, 200 candidates completed in 438.27 seconds, about 7 minutes 18 seconds, with 90 executed provider queries out of 372 planned.
- Query Group Contribution Report now hides unexecuted zero-row groups from UI/CSV exports, keeping benchmark reports focused on groups that actually ran or produced lift.
- Benchmark Summary now compares recent runs in the UI and CSV by duration, executed/planned calls, provider lift, and top query groups.
- Benchmark Summary now includes quick filters for all runs, same role family, same location, and Max 200 runs; CSV export follows the active filter.
- Role presets and semantic families now include Business Analysis, Data / BI Analytics, Product / Project Management, Architecture / Leadership, and UX / Product Design.
- Executed-query audit files can be generated from saved runs to inspect the exact provider queries and pagination offsets that were sent.
- Server log files are ignored by Git.

In progress:

- Owner-led search-engine review, including Serper validation.
- Next provider evaluation shortlist: SearchAPI.io and Exa.
- Strict location filtering and UX validation on real Houston searches.
- Provider-quality benchmarking across Standard, Medium, Extended, and Max search depths.
- High-recall search planning for 100/200-candidate runs, including evidence-first wave tuning and Max budget caps. Implementation is in place; next step is real-run validation.
- Adaptive-wave intelligence validation on real 100/200-candidate searches, including whether reranking and conservative replacement improve unique lift.
- Resume review UX.
- Frontend simplification so the left panel stays usable as the workflow grows.

Next recommended product step:

- Run side-by-side benchmarks for Standard, Medium, Extended, and Max on the same requirement. Use the Provider Contribution Report, saved diagnostics, and executed-query audits to compare actual provider contribution, not just planned query counts.
- Run the first real evidence-first validation search on May 13, 2026: use a known hard role/location case, preferably Houston Front Office / ETRM, at Max depth with 200 target candidates.
- Generalize evidence-first query generation across all Role Groups, while keeping Energy / ETRM as the first specialized evidence pattern. Add specialized patterns family-by-family as owner-provided recruiting/domain knowledge arrives.
- Benchmark Max early-stop behavior against selected target and planned call cap so high-recall searches remain credit-safe.
- After the validation run, inspect Technical reports for provider lift, query-group lift, strict-location rejects, stop reason, and whether Evidence Expansion ran or was skipped.
- Benchmark dynamic reranking and conservative replacement after the evidence-first wave split lands.
- Test the next provider shortlist with the same X-Ray query set and compare raw LinkedIn URLs, strict-location survivors, deduped candidates, cost, and pagination behavior.

## Next Implementation Plan: Evidence-first Search Waves

Estimated time for first useful implementation: 2-4 hours.

Production-clean version with broader tests and polished reporting: about half a day.

Goal:

- Replace the current title-first search behavior with an evidence-first wave plan.
- Make evidence-first the general query planning model for all Role Groups, with role-specific specialized evidence patterns added over time.
- Keep the existing provider pipeline, strict location filtering, dedupe, scoring, and result UI.
- Avoid silent credit overuse by making Max stop at target, planned call cap, or exhausted plan.

Implementation steps:

1. Query planner wave model, about 30-45 minutes. Completed.
   Added explicit wave types: `evidence_core`, `title_focus`, and `evidence_expansion`.

2. Energy / ETRM evidence patterns, about 45-75 minutes. Completed.
   Added query groups for BA/function evidence, vendor/tool evidence, domain evidence, and high-recall consultant/SME/lead/developer evidence.

3. Search-depth mapping, about 30-45 minutes. Completed.
   Standard, Medium, and Extended now run Evidence Core followed by Title Focus. Max now runs Evidence Core, Title Focus, and Evidence Expansion only if the target is not yet filled.

4. General evidence pattern for all Role Groups, about 60-120 minutes. Completed.
   Added a generic evidence builder so non-Energy families also get Evidence Core, Title Focus, and Evidence Expansion. Energy / ETRM remains the first specialized evidence pattern, and additional specialized patterns will be added as owner knowledge is supplied.

5. Max stop conditions, about 20-30 minutes. Completed.
   Stops when `accepted_candidates >= selected_result_limit`, primary search calls reach `planned_call_cap`, or all planned waves/pages are exhausted. Location verification calls remain tracked separately.

6. Audit/report updates, about 30-45 minutes. Completed.
   Search Explanation and Technical reports show wave labels, planned calls, budgeted calls, executed calls, stop reason, and whether Evidence Expansion ran or was skipped.

7. Local verification, about 20-40 minutes. Completed.
   Python compile checks, frontend syntax checks, and dry-run query-plan inspection pass before spending search provider credits.

8. Real validation run, planned for May 13, 2026.
   Run a hard 200-candidate Max search, then inspect Search Explanation, Provider Contribution Report, Query Group Contribution Report, Adaptive Waves, executed queries, stop reason, and Evidence Expansion status.

First-version acceptance criteria:

- Houston Front Office / ETRM search preview shows Evidence Core and Title Focus in Standard/Medium/Extended.
- Max preview shows Evidence Core, Title Focus, and conditional Evidence Expansion.
- Generated sample queries include terms such as `ETRM`, `CTRM`, `Endur`, `OpenLink`, `RightAngle`, `Allegro`, `Trade Capture`, `Trading Systems`, `Business Analyst`, `BA`, `Consultant`, `SME`, `Lead`, `Architect`, and `Developer` where appropriate.
- Max reports target/call-cap/exhausted-plan stop behavior.
- Existing Java/QA/Data family searches still generate valid query plans and do not break.
- Java/QA/Data/Product/etc. Role Groups use the general evidence-first pattern, while specialized family patterns can override/enrich the generic groups when we have better domain knowledge.
