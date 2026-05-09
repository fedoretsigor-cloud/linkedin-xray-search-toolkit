import requests


SERPAPI_URL = "https://serpapi.com/search.json"
BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"
SERPER_SEARCH_URL = "https://google.serper.dev/search"
YOU_SEARCH_URL = "https://ydc-index.io/v1/search"


def search_serpapi(api_key, query, num, start=None):
    params = {"key": api_key, "engine": "google", "q": query, "num": num}
    if start is not None:
        params["start"] = start
    response = requests.get(SERPAPI_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def search_bing_serpapi(api_key, query, num, first=None):
    params = {"api_key": api_key, "engine": "bing", "q": query, "count": num}
    if first is not None:
        params["first"] = first
    response = requests.get(SERPAPI_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def search_brave(api_key, query, num):
    headers = {"Accept": "application/json", "X-Subscription-Token": api_key}
    params = {"q": query, "count": num}
    response = requests.get(BRAVE_SEARCH_URL, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def search_serper(api_key, query, num, page=None):
    headers = {"Content-Type": "application/json", "X-API-KEY": api_key}
    payload = {"q": query, "num": num}
    if page is not None:
        payload["page"] = page
    response = requests.post(SERPER_SEARCH_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def search_you(api_key, query, num, offset=None):
    headers = {"X-API-Key": api_key}
    params = {
        "query": query,
        "count": min(int(num), 100),
        "safesearch": "moderate",
    }
    if offset is not None:
        params["offset"] = offset
    response = requests.get(YOU_SEARCH_URL, headers=headers, params=params, timeout=45)
    response.raise_for_status()
    return response.json()


def infer_query_domains(query):
    domains = []
    for token in str(query or "").split():
        cleaned = token.strip('"()')
        if not cleaned.lower().startswith("site:"):
            continue
        domain = cleaned.split(":", 1)[1].strip().strip("/")
        domain = domain.split("/", 1)[0].lower()
        if domain and domain not in domains:
            domains.append(domain)
    return domains
