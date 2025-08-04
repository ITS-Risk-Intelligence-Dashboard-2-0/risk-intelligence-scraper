import socket
import requests
import os
import json
import shutil
from urllib.parse import urlparse

from celery import shared_task, chain, group
from playwright.sync_api import sync_playwright

from web_scraper_project.celery import app

from maizey_api.api_call import create_conversation, call_api

from scraper.crawler import scrape_links
from scraper.basic_filter import filter_scraped_urls
from scraper.pdf_scraper import scrape_pdf_text
from scraper.retrieval import retrieve_page, retrieve_pdf
from scraper.maizey_filter import maizey_filter_content

from shared.core_lib.db_utils import establish_connection

#from gdrive.api import authenticate_drive, upload_pdf_to_drive


def batch_items(arr, batch_count):
    batches = [[] for _ in range(batch_count)]

    for i in range(len(arr)):
        chunk = i % batch_count
        batches[chunk].append(arr[i])

    return batches

def retrieve_browser_link(browser):
    try:
        browser_ip = socket.gethostbyname(browser)
        response = requests.get(f"http://{browser_ip}:9222/json/version")
        return response.json()["webSocketDebuggerUrl"]
    except socket.gaierror as e:
        print(f"DNS resolution failed: {e}")
        return None
    except Exception as e:
        print(e)
        return None

def wipe_folder(path):
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  # remove file or symlink
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  # remove directory and its contents
        except Exception as e:
            print(f'Failed to delete {file_path}: {e}')


@shared_task(name="web_scraper.tasks.start_scraping_workflow")
def start_scraping_workflow(sources_data):
    """
    This is a meta-task that defines and dispatches the entire workflow.
    It chains the initial scrape with the main processing task.
    """

    wipe_folder("/app/pages")

    browser_connection = retrieve_browser_link("browser")
    if browser_connection is None:
        print("ERROR. Could not connect to browser instance!")
        return

    workflow = chain(
        scrape_links.s(browser_connection, sources_data),
        process_url_list.s(browser_connection)
    )
    workflow.delay()
    print("Scraping workflow initiated.")

@shared_task
def process_url_list(discovered_paths, browser_connection):
    """
    Receives a list of URLs and creates a group of parallel processing chains.
    Each chain validates one URL and then generates a PDF for it.
    """
    urls, pdfs, excluded = discovered_paths

    print(f"Number of urls: {len(urls)}")
    print(f"Number excluded: {len(excluded)}")

    categories_config = []
    with open("./categories_config.json", "r") as f:
        categories_config = json.load(f)

    # dispatch url scraping pipeline
    batched_urls = batch_items(urls, 1)
    url_group = group(
        chain(
            filter_scraped_urls.s((batch, browser_connection)),
            maizey_filter_content.s(categories_config),
            retrieve_page.s(browser_connection)
        ) for batch in batched_urls
    )

    url_group.delay()

    # dispatch pdf scraping pipeline
    pdf_group = group(
        chain(
            scrape_pdf_text.s(pdf),
            maizey_filter_content.s(categories_config),
            retrieve_pdf.s()
        ) for pdf in pdfs
    )

    pdf_group.delay()
