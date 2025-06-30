from celery import shared_task
import requests
from bs4 import BeautifulSoup
from web_scraper_app.scraper.tasks import generate_pdf_task

@shared_task
def scrape_google_links():
    source_hubs = ["https://www.cnn.com", "https://www.foxnews.com"] # for testing purposes

    sources = set(source_hubs)

    while len(sources) > 0:
        curr_source = sources.pop()

        curr_source_parsed_url = urlparse(curr_source)
        curr_source_scheme = curr_source_parsed_url.scheme
        curr_source_netloc = curr_source_parsed_url.netloc

        response = requests.get(curr_source)

        soup = BeautifulSoup(response.text, "html.parser")

        anchor_tags = soup.find_all("a")

        for anchor in anchors:
            if not anchor.has_attr("href"):
                continue

            scraped_url = urlparse(anchor.get("href"))
            url_path = scraped_url.path
            base_path = url.netloc
            if scraped_url.netloc != curr_source_netloc and base_path != "":
                continue

            fullurl = urljoin(curr_source_netloc, scraped_url.path)

            generate_pdf_task.delay(fullurl)

    #response = requests.get(url)
    #soup = BeautifulSoup(response.text, "html.parser")
    #links = soup.find_all("a")
    #hrefs = [link.get("href") for link in links if link.get("href")]
    #return hrefs
    return []

