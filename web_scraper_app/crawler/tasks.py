from celery import shared_task
import requests
from bs4 import BeautifulSoup
from web_scraper_app.scraper.tasks import generate_pdf_task

@shared_task
def scrape_google_links():
    url = "https://www.google.com/"
    generate_pdf_task.delay(url)
    #response = requests.get(url)
    #soup = BeautifulSoup(response.text, "html.parser")
    #links = soup.find_all("a")
    #hrefs = [link.get("href") for link in links if link.get("href")]
    #return hrefs
    return []
