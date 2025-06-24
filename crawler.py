import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json

news_articles = set()

def news_crawler(hub, news_paths, fullpath=False):

    google_news_req = requests.get(hub)

    soup = BeautifulSoup(google_news_req.text, "html.parser")

    anchors = soup.find_all("a")

    for anchor in anchors:
        if not anchor.has_attr("href"):
            continue

        url = anchor.get("href")

        for path in news_paths:
            if urlparse(url).path.startswith(path):
                if fullpath:
                    full_url = urljoin(hub, urlparse(url).path)
                    news_articles.add(full_url)
                else:
                    full_url = urljoin(hub, url)
                    news_articles.add(full_url)

def main():
    with open("crawlerconfig.json", "r") as f:
        data = json.load(f)

        for hub in data:
            news_crawler(hub["url"], hub["paths"], hub["fullpath"])

    for article in news_articles:
        # push to celery job
        print(article)

main()
