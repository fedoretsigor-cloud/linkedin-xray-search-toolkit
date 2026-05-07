import re
from html import unescape
from urllib.parse import urlparse

import requests

from src.text_utils import clean_text


MAX_REQUIREMENT_TEXT_CHARS = 18000


def validate_public_url(url):
    parsed = urlparse(clean_text(url))
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RuntimeError("Requirement URL must be a valid http or https URL")
    return parsed.geturl()


def html_to_text(html):
    text = re.sub(r"(?is)<(script|style|noscript|svg).*?>.*?</\1>", " ", html or "")
    text = re.sub(r"(?is)<br\s*/?>", "\n", text)
    text = re.sub(r"(?is)</(p|div|li|h[1-6]|tr)>", "\n", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return clean_text(text)


def fetch_requirement_text(url, timeout=20):
    safe_url = validate_public_url(url)
    headers = {
        "User-Agent": "EngineerSearchAI/1.0 (+public requirement intake)",
        "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.8",
    }
    response = requests.get(safe_url, headers=headers, timeout=timeout)
    response.raise_for_status()

    content_type = response.headers.get("content-type", "").lower()
    if "pdf" in content_type:
        raise RuntimeError("PDF requirement pages are not supported yet. Please use a public HTML page.")

    if "html" in content_type or "<html" in response.text[:500].lower():
        text = html_to_text(response.text)
    else:
        text = clean_text(response.text)

    if len(text) < 120:
        raise RuntimeError("Could not extract enough readable text from the requirement URL")

    return {
        "url": safe_url,
        "title": extract_page_title(response.text),
        "text": text[:MAX_REQUIREMENT_TEXT_CHARS],
        "truncated": len(text) > MAX_REQUIREMENT_TEXT_CHARS,
    }


def extract_page_title(html):
    match = re.search(r"(?is)<title[^>]*>(.*?)</title>", html or "")
    if not match:
        return ""
    return clean_text(unescape(re.sub(r"<[^>]+>", " ", match.group(1))))
