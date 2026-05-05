import requests

TAVILY_SEARCH_URL = "https://api.tavily.com/search"


class TavilyClient:
    def __init__(self, api_key, timeout=30):
        self.api_key = (api_key or "").strip()
        self.timeout = timeout

    def ensure_configured(self):
        if not self.api_key:
            raise RuntimeError("Missing TAVILY_API_KEY in .env")

    def search(self, query, num, search_depth="basic", topic="general"):
        self.ensure_configured()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "query": query,
            "search_depth": search_depth,
            "topic": topic,
            "max_results": num,
            "include_answer": False,
            "include_raw_content": False,
        }
        response = requests.post(
            TAVILY_SEARCH_URL,
            headers=headers,
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()


def search_tavily(api_key, query, num, timeout=30):
    client = TavilyClient(api_key=api_key, timeout=timeout)
    return client.search(query=query, num=num)
