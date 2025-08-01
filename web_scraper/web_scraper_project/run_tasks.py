import socket
import requests
import os
import json
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

@shared_task(name="web_scraper.tasks.start_scraping_workflow")
def start_scraping_workflow(sources_data):
    """
    This is a meta-task that defines and dispatches the entire workflow.
    It chains the initial scrape with the main processing task.
    """
    #conn, cursor = establish_connection()
    #find_table(cursor)
    #seed_sources(conn, cursor)
    #source_hubs = retrieve_sources(cursor)
    #cursor.close()
    #conn.close()

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

    # categories_config = [
    #     {
    #         "category_name": "AI",
    #         "min_relevance_threshold": 0.8,
    #     },
    #     {
    #         "category_name": "Compliance",
    #         "min_relevance_threshold": 0.8,
    #     },
    #     {
    #         "category_name": "Crisis Management",
    #         "min_relevance_threshold": 0.8,
    #     },
    #     {
    #         "category_name": "Cryptocurrency",
    #         "min_relevance_threshold": 0.8,
    #     },
    #     {
    #         "category_name": "Culture",
    #         "min_relevance_threshold": 0.8,
    #     },
    #     {
    #         "category_name": "Cybersecurity",
    #         "min_relevance_threshold": 0.8,
    #     },
    #     {
    #         "category_name": "Data Privacy",
    #         "min_relevance_threshold": 0.8,
    #     },
    #     {
    #         "category_name": "DEI",
    #         "min_relevance_threshold": 0.8,
    #     },
    #     {
    #         "category_name": "Emerging",
    #         "min_relevance_threshold": 0.8,
    #     },
    #     {
    #         "category_name": "ESG",
    #         "min_relevance_threshold": 0.8,
    #     },
    #     {
    #         "category_name": "Geopolitical",
    #         "min_relevance_threshold": 0.8,
    #     },
    #     {
    #         "category_name": "Healthcare",
    #         "min_relevance_threshold": 0.8,
    #     },
    #     {
    #         "category_name": "International",
    #         "min_relevance_threshold": 0.8,
    #     },
    #     {
    #         "category_name": "Mental Health",
    #         "min_relevance_threshold": 0.8,
    #     },
    #     {
    #         "category_name": "NIL",
    #         "min_relevance_threshold": 0.8,
    #     },
    #     {
    #         "category_name": "Physical Security Threat",
    #         "min_relevance_threshold": 0.8,
    #     },
    #     {
    #         "category_name": "Policy",
    #         "min_relevance_threshold": 0.8,
    #     },
    #     {
    #         "category_name": "Post-Election",
    #         "min_relevance_threshold": 0.8,
    #     },
    #     {
    #         "category_name": "Prop 2",
    #         "min_relevance_threshold": 0.8,
    #     },
    #     {
    #         "category_name": "Residential Life",
    #         "min_relevance_threshold": 0.8,
    #     },
    #     {
    #         "category_name": "Safety",
    #         "min_relevance_threshold": 0.8,
    #     },
    #     {
    #         "category_name": "Sexual Misconduct",
    #         "min_relevance_threshold": 0.8,
    #     },
    #     {
    #         "category_name": "Succession Planning",
    #         "min_relevance_threshold": 0.8,
    #     },
    #     {
    #         "category_name": "Supply Chain",
    #         "min_relevance_threshold": 0.8,
    #     },
    #     {
    #         "category_name": "Third Parties",
    #         "min_relevance_threshold": 0.8,
    #     },
    #     {
    #         "category_name": "Title IX",
    #         "min_relevance_threshold": 0.8,
    #     },
    #     {
    #         "category_name": "Weather",
    #         "min_relevance_threshold": 0.8,
    #     },
    #     {
    #         "category_name": "Workforce Management",
    #         "min_relevance_threshold": 0.8,
    #     },
    #     {
    #         "category_name": "Profiles",
    #         "min_relevance_threshold": 0.8,
    #     }
    # ]

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
