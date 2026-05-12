import time

import requests

TAVILY_SEARCH_URL = "https://api.tavily.com/search"
TRANSIENT_HTTP_STATUSES = {408, 429, 500, 502, 503, 504}


class TavilyClient:
    def __init__(self, api_key, timeout=45, retries=2, retry_delay=0.75):
        self.api_key = (api_key or "").strip()
        self.timeout = timeout
        self.retries = max(0, int(retries or 0))
        self.retry_delay = max(0, float(retry_delay or 0))

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
        for attempt in range(self.retries + 1):
            try:
                response = requests.post(
                    TAVILY_SEARCH_URL,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.json()
            except (requests.Timeout, requests.ConnectionError):
                if attempt >= self.retries:
                    raise
            except requests.HTTPError as exc:
                status_code = response.status_code
                if status_code in TRANSIENT_HTTP_STATUSES and attempt < self.retries:
                    self.sleep_before_retry(attempt)
                    continue
                message = response.text.strip()
                if len(message) > 500:
                    message = message[:500] + "..."
                raise RuntimeError(f"Tavily search failed ({status_code}): {message}") from exc

            self.sleep_before_retry(attempt)

        raise RuntimeError("Tavily search failed after retries")

    def sleep_before_retry(self, attempt):
        if self.retry_delay:
            time.sleep(self.retry_delay * (attempt + 1))


def search_tavily(api_key, query, num, timeout=45, retries=2):
    client = TavilyClient(api_key=api_key, timeout=timeout, retries=retries)
    return client.search(query=query, num=num)
