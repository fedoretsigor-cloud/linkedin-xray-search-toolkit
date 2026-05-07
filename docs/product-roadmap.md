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

Status: Partially done.

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
- The current confirmation is still lightweight: applying the brief fills the existing Search Builder.

Remaining work:

- Add a dedicated confirmed brief state.
- Add explicit "Confirm brief" / "Revise brief" workflow.
- Store the confirmed brief with the search run or sourcing project.

### Phase 3: Search Strategy Agent

Status: Partially done.

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

Remaining work:

- Show generated query plan in the UI before search.
- Explain recall vs precision tradeoffs.
- Allow the human to approve or edit query groups before running search.

### Phase 4: Candidate Search

Status: Done in MVP, needs sourcing-project upgrade.

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
- Hybrid role presets and editable role variants are implemented.
- Devpost-specific normalization now avoids treating project titles as candidate names.

Remaining work:

- Convert standalone search runs into sourcing projects linked to requirement briefs.
- Store full query plans and confirmed search strategy.
- Improve source-specific search behavior per source.

### Phase 5: Manual Profile Review

Status: Not started.

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

### Phase 6: Candidate Communication Tracker

Status: Not started.

Once the human starts working on a candidate, create a candidate workflow record.

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

### Phase 7: Resume Review

Status: Not started.

Allow resume upload.

The human may remove personal data before uploading.

The system compares the resume against:

- Original requirement brief.
- Confirmed search strategy.
- Profile analysis.
- Candidate communication notes.

Output:

- Fit decision.
- Evidence table.
- Missing evidence.
- Contradictions between profile and resume.
- Clarifying questions.
- Recommended next action.

### Phase 8: Decision Memory

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

### Phase 9: Conversational Sourcing Copilot

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
4. Partially done: Link extracted brief to the existing search builder.
5. Partially done: Add compact search strategy generation for Tavily.
6. Next: Add explicit confirmation screen/state before search.
7. Next: Store confirmed brief and generated query plan with each search run.
8. Next: Add manual profile review textarea.
9. Later: Add candidate status tracking.
10. Later: Add resume upload and resume analysis.
11. Later: Add conversational sourcing copilot on top of stable workflow actions.

## Current Decision

The idea is strong and should be pursued as a staged product.

The immediate next architectural direction is to evolve the current search app into a human-in-the-loop AI sourcing workflow, while keeping LinkedIn interaction manual and safe.

The conversational agent idea is valuable and should remain in the roadmap. It should be implemented as a later interface layer over stable workflow actions, not as an early replacement for structured screens.

## Progress Snapshot

Last updated: 2026-05-07.

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

In progress:

- Human confirmation between extracted brief and search.
- Search strategy visibility in UI.
- Project-level persistence for requirement brief and query plan.

Next recommended product step:

- Build a confirmed brief / search strategy review screen before running search.
