from celery import shared_task
import requests
from bs4 import BeautifulSoup
from scraper.filter import filter_scraped_urls
from urllib.parse import urlparse, urlunparse

def build_url(current_url, scraped_url):
    return urlunparse(("https", current_url.netloc, scraped_url.path, '', '', ''))

def same_domain(netloc1, netloc2):
    if netloc1 == '' or netloc2 == '':
        return True

    domain_levels1 = netloc1.split('.')
    domain_levels2 = netloc2.split('.')

    try:
        same_top_domain = domain_levels1[-1] == domain_levels2[-1]
        same_second_domain = domain_levels1[-2] == domain_levels2[-2]
    except:
        return False

    return same_top_domain and same_second_domain

def analyze_last_path(chunk):
    words = chunk.split("-")
    if len(words) < 3:
        return False

    for word in words:
        for c in word:
            if c >= 'a' and c <= 'z':
                continue

            if c == '-' or c == '.':
                continue

            return False

    return True

def probably_news(path):
    path_chunks = path.split("/")
    is_article = analyze_last_path(path_chunks[-1])

    if not is_article:
        return None

    return "/".join(path_chunks[:-1])

@shared_task
def scrape_google_links():
    source_hubs = ["https://www.cnn.com", "https://www.foxnews.com"] # for testing purposes

    sources = set(source_hubs)

    results = []
    while len(sources) > 0:
        curr_source = sources.pop()

        curr_source_parsed = urlparse(curr_source)

        try:
            response = requests.get(curr_source)
        except:
            continue

        parsed_html = BeautifulSoup(response.text, "html.parser")

        anchor_tags = parsed_html.find_all("a")

        for anchor in anchor_tags:
            if not anchor.has_attr("href"):
                continue

            scraped_url = urlparse(anchor.get("href"))
            if not same_domain(scraped_url.netloc, curr_source_parsed.netloc):
                continue

            if probably_news(scraped_url.path):
                final_url = build_url(curr_source_parsed, scraped_url)
                filter_scraped_urls.delay(final_url)

    return []

