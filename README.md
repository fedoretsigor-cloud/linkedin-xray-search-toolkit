# LinkedIn X-Ray Search Toolkit

Portable toolkit for finding IT profiles on LinkedIn via X-Ray search without using the LinkedIn API.

## What It Does

- builds X-Ray queries for LinkedIn profile search;
- sends those queries through a search provider;
- saves results to CSV;
- supports batch search across multiple titles, skills, and locations;
- keeps secrets local via `.env`.

## Current Search Providers

- `SerpApi` - recommended for Google-style X-Ray search
- `Brave Search API` - optional alternative

## Project Structure

- `src/xray_search.py` - simple query generator
- `src/google_xray_to_csv.py` - search + CSV export
- `examples/titles.txt` - sample titles list
- `examples/skills.txt` - sample skills list
- `examples/locations.txt` - sample locations list
- `.env.example` - config template
- `requirements.txt` - Python dependencies

## Quick Start

1. Create a virtual environment:

```powershell
python -m venv .venv
```

2. Install dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

3. Create your local config:

```powershell
Copy-Item .env.example .env
```

4. Add your `SERPAPI_API_KEY` to `.env`.

5. Generate a simple X-Ray query:

```powershell
.\.venv\Scripts\python.exe .\src\xray_search.py --title "python developer" --skill django --location germany
```

6. Run search and save CSV:

```powershell
.\.venv\Scripts\python.exe .\src\google_xray_to_csv.py --title "python developer" --skill django --location germany --output .\output\linkedin_profiles.csv
```

## Batch Search

You can pass repeated flags:

```powershell
.\.venv\Scripts\python.exe .\src\google_xray_to_csv.py `
  --title "python developer" `
  --title "backend developer" `
  --skill django `
  --skill fastapi `
  --location germany `
  --location poland `
  --output .\output\batch_profiles.csv
```

You can also use text files:

```powershell
.\.venv\Scripts\python.exe .\src\google_xray_to_csv.py `
  --titles-file .\examples\titles.txt `
  --skills-file .\examples\skills.txt `
  --locations-file .\examples\locations.txt `
  --output .\output\batch_profiles.csv
```

The script deduplicates results by profile URL and writes helpful columns like:

- `query`
- `title_input`
- `skill_input`
- `location_input`
- `name`
- `headline`
- `title`
- `link`
- `snippet`
- `display_link`
- `source`

## Why Not Google Custom Search JSON API

Google's `Custom Search JSON API` is closed to new customers, so this project uses alternative search providers instead.

Source:
- [Custom Search JSON API overview](https://developers.google.com/custom-search/v1/overview)

## Configuration

Example `.env` for SerpApi:

```dotenv
SEARCH_PROVIDER=serpapi
SEARCH_RESULTS_PER_QUERY=10
SERPAPI_API_KEY=your_serpapi_key
BRAVE_SEARCH_API_KEY=
```

## Move To Another Computer

1. Clone the repository.
2. Create `.env` from `.env.example`.
3. Create `.venv`.
4. Install dependencies.
5. Add your API key.
6. Run the same commands.

Local secrets and outputs are not committed:

- `.env`
- `.venv/`
- `output/`

## GitHub Workflow

Typical setup on a new machine:

```powershell
git clone https://github.com/fedoretsigor-cloud/linkedin-xray-search-toolkit.git
cd linkedin-xray-search-toolkit
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

## Useful Links

- [SerpApi](https://serpapi.com/)
- [SerpApi Google Search API](https://serpapi.com/search-api)
- [Brave Search API](https://brave.com/search/api/)
- [Google API keys docs](https://cloud.google.com/docs/authentication/api-keys)
