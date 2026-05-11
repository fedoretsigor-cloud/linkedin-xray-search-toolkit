# LinkedIn X-Ray Search Toolkit

Portable toolkit for finding IT profiles on LinkedIn via X-Ray search without using the LinkedIn API.

## What It Does

- builds X-Ray queries for LinkedIn profile search;
- sends those queries through a search provider;
- saves results to CSV;
- supports batch search across multiple titles, skill groups, locations, and profile sites;
- keeps secrets local via `.env`.

## Current Search Providers

- `SerpApi` - recommended for Google-style X-Ray search
- `Tavily` - practical alternative with free monthly credits
- `Serper` - optional Google-style search provider

## Make It Public

The easiest way to make the app available from any computer is Render.

This repo now includes `render.yaml`, so deployment is simple:

1. Push your latest code to GitHub.
2. Create an account at [Render](https://render.com/).
3. In Render, choose `New` -> `Blueprint`.
4. Connect this GitHub repository.
5. Render will detect `render.yaml`.
6. In environment variables, set:
   - `TAVILY_API_KEY`
7. Deploy.

Render will build with:

- `pip install -r requirements.txt`

and start with:

- `gunicorn app:app`

After deploy, Render gives you a public `onrender.com` URL.

Note:

- local `data/` storage is ephemeral on Render, so saved runs may disappear after redeploy/restart
- for persistent history later, move search history to a database

## Project Structure

- `src/xray_search.py` - simple query generator
- `src/google_xray_to_csv.py` - search + CSV export
- `examples/titles.txt` - sample titles list
- `examples/skills.txt` - sample skills list
- `examples/locations.txt` - sample locations list
- `run_batch_search.ps1` - quick batch launcher for PowerShell
- `run_batch_search.cmd` - quick batch launcher for Command Prompt
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

4. Add your provider key to `.env`.

5. Generate a simple X-Ray query:

```powershell
.\.venv\Scripts\python.exe .\src\xray_search.py --title "python developer" --skill django --location germany
```

6. Run search and save CSV:

```powershell
.\.venv\Scripts\python.exe .\src\google_xray_to_csv.py --title "python developer" --skill django --location germany --output .\output\linkedin_profiles.csv
```

## Phase 1 Web App

Run the local MVP interface:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\START_PHASE1_APP.cmd
```

Then open:

```text
http://127.0.0.1:5000
```

Phase 1 includes:

- Search Builder
- Candidate Results table
- AI Candidate Profile side panel
- saved local search runs

## Batch Search

You can pass repeated flags:

```powershell
.\.venv\Scripts\python.exe .\src\google_xray_to_csv.py `
  --title "python developer" `
  --title "backend developer" `
  --skill "python | django | postgresql" `
  --skill "python | fastapi | aws" `
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

Or just run one of the helper launchers:

```powershell
.\run_batch_search.ps1
```

```cmd
run_batch_search.cmd
```

By default the launcher currently searches:

- LinkedIn
- Facebook

The script deduplicates results by profile URL and writes recruiter-friendly columns like:

- `Source Site`
- `Candidate Name`
- `Profile URL`
- `Role`
- `Technology`
- `Location`
- `Short Description`

## Skill Group Format

Each line in `examples/skills.txt` is treated as one full required skill set.

Example:

```text
java | javascript | oracle
python | django | postgresql
```

That means the query is built with all listed technologies together, not one by one.

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
```

Example `.env` for Tavily:

```dotenv
SEARCH_PROVIDER=tavily
SEARCH_RESULTS_PER_QUERY=10
SERPAPI_API_KEY=
TAVILY_API_KEY=your_tavily_api_key
```

## Indexed Profile Data We Can Capture

From the search result itself, we can usually capture:

- search query inputs that found the profile;
- profile name inferred from result title;
- profile headline inferred from result title;
- LinkedIn profile URL and slug;
- LinkedIn regional subdomain such as `de`, `uk`, or `www`;
- result rank in search;
- result snippet text;
- displayed link;
- provider-specific source/date fields;
- redirect, cached, related-pages, favicon, and thumbnail links when available;
- rich snippet, sitelinks, and extensions when provided by the search provider.

This is indexed search-result metadata, not full LinkedIn profile scraping.

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
- [Serper](https://serper.dev/)
- [Tavily Search API](https://docs.tavily.com/api-reference/endpoint/search)
- [Google API keys docs](https://cloud.google.com/docs/authentication/api-keys)
