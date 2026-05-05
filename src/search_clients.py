import requests


SERPAPI_URL = "https://serpapi.com/search.json"
BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"


def search_serpapi(api_key, query, num):
    params = {"key": api_key, "engine": "google", "q": query, "num": num}
    response = requests.get(SERPAPI_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def search_brave(api_key, query, num):
    headers = {"Accept": "application/json", "X-Subscription-Token": api_key}
    params = {"q": query, "count": num}
    response = requests.get(BRAVE_SEARCH_URL, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    return response.json()
