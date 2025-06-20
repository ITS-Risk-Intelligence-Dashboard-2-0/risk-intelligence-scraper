from celery import shared_task
import requests
from bs4 import BeautifulSoup

@shared_task
def scrape_google_links():
    url = "https://www.google.com/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    links = soup.find_all("a")
    hrefs = [link.get("href") for link in links if link.get("href")]
    return hrefs
