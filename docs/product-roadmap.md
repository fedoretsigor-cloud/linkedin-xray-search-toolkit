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

The agent should not:

- Automatically use a human's logged-in LinkedIn session.
- Use LinkedIn cookies or browser automation to scrape profiles.
- Mass-open profiles as a bot.
- Extract private or login-gated data.
- Send messages to candidates without human approval.

## Product Phases

### Phase 1: Requirement Intake

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

### Phase 2: Human Confirmation

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

### Phase 3: Search Strategy Agent

Generate a search plan from the confirmed brief:

- Role variants.
- Stack variants.
- Source selection.
- Query count.
- Query examples.
- Recall vs precision tradeoff.

The system should explain why it chose the queries.

### Phase 4: Candidate Search

Run public source search using the existing search pipeline.

Save each search as a sourcing project or search run:

- Requirement brief.
- Confirmed search strategy.
- Queries used.
- Candidates found.
- Search source evidence.

### Phase 5: Manual Profile Review

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

Store a complete candidate decision trail:

- Why this candidate was selected.
- What evidence supported the fit.
- What risks were found.
- What questions were asked.
- What the candidate answered.
- What the resume confirmed or contradicted.
- Final recommendation.

This makes the system useful as a sourcing memory layer, not just a search interface.

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

## Compliance And Safety Boundaries

The safe architecture is:

```text
Public requirement URL
-> AI requirement extraction
-> human confirmation
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

1. Add a `docs/` roadmap and keep this plan as the product source of truth.
2. Add requirement URL intake and public page fetch.
3. Add requirement brief extraction.
4. Add a confirmation screen before search.
5. Link confirmed brief to the existing search builder.
6. Add manual profile review textarea.
7. Add candidate status tracking.
8. Add resume upload and resume analysis.

## Current Decision

The idea is strong and should be pursued as a staged product.

The immediate next architectural direction is to evolve the current search app into a human-in-the-loop AI sourcing workflow, while keeping LinkedIn interaction manual and safe.
