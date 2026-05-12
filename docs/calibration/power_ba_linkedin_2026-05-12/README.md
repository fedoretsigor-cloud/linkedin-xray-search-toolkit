# Power BA LinkedIn Calibration Dataset

Status: local calibration dataset.

Created: 2026-05-12.

Purpose:

- Preserve the manually reviewed LinkedIn reference list for the Houston Front Office / Power BA / ETRM search.
- Use it as a calibration set when tuning search waves, semantic families, title logic, scoring gates, and LinkedIn-like adjacent title expansion.
- Compare future search runs against this list manually or with small local analysis scripts.

Files:

- `86_power_ba_linkedin.csv` - structured list transcribed from LinkedIn screenshots.
- `86_power_ba_linkedin.md` - human-readable version of the same list.

Dataset shape:

- `number`
- `name`
- `linkedin_url`
- `headline`
- `location_industry`
- `source_image`

Known limitations:

- `linkedin_url` is blank because the screenshots did not expose profile URLs.
- Matching is currently name-based, so overlap can be undercounted when names are abbreviated, duplicated, or formatted differently.
- The dataset represents LinkedIn visible/recruiter-style results, not a public web/X-ray search result.
- Some evidence visible in LinkedIn screenshots may come from private or authenticated profile fields that public search providers cannot access.

Current baseline comparison:

- Reference LinkedIn list: 86 names.
- Saved public/X-ray run: `30b87d9e92`.
- Public/X-ray run size: 186 candidates.
- Exact normalized-name overlap: 13 names.
- Missing from public/X-ray run by exact normalized-name comparison: 73 names.

How to use:

1. Run a new search experiment.
2. Export or load the saved run candidate list.
3. Compare normalized candidate names against `86_power_ba_linkedin.csv`.
4. Inspect which query groups and waves produced the overlaps.
5. Tune Wave 2 and scoring only after confirming whether overlap and top-candidate quality improved.

Product decision:

- Keep this as an internal/manual calibration dataset for now.
- Do not add benchmark import/reporting to the main product UI until this becomes a recurring user-facing need.
