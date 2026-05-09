import requests


SERPAPI_URL = "https://serpapi.com/search.json"
BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"
SERPER_SEARCH_URL = "https://google.serper.dev/search"


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
