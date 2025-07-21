from celery import shared_task
import requests
from bs4 import BeautifulSoup

@shared_task
def filter_scraped_urls(url):
    """
    Processes a SINGLE URL. If its content is substantial, it returns the URL
    to be passed to the next task in a chain. Otherwise, it returns None.
    """
    print(f"Filtering: {url}")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Could not fetch or invalid response for {url}: {e}")
        return None

    parsed_html = BeautifulSoup(response.text, "html.parser")

    paragraphs = parsed_html.find_all("p")
    if not paragraphs:
        print(f"Rejected: No paragraphs found in {url}")
        return None

    page_content = " ".join(p.get_text().strip() for p in paragraphs)

    if len(page_content) > 200:
        print(f"Accepted: {url} (Content length: {len(page_content)})")
        return url
    else:
        print(f"Rejected: Content too short in {url} (Length: {len(page_content)})")
        return None