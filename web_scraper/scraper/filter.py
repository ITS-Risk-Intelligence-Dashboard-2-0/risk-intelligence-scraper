from celery import shared_task
import requests
from bs4 import BeautifulSoup

@shared_task
def filter_scraped_urls(url):
    response = requests.get(url)
    parsed_html = BeautifulSoup(response.text, "html.parser")

    paragraphs = parsed_html.find_all("p")
    page_texts = []
    for paragraph in paragraphs:
        text = paragraph.get_text().strip()
        page_texts.append(text)

    page_content = " ".join(page_texts)

    if len(page_content) > 200:
        print(f"submit to next stage in pipeline {url}")