from celery import shared_task, chain, group
from scraper.crawler import scrape_links
from scraper.filter import filter_scraped_urls
import time

@shared_task(name="web_scraper.tasks.start_scraping_workflow")
def start_scraping_workflow():
    """
    This is a meta-task that defines and dispatches the entire workflow.
    It chains the initial scrape with the main processing task.
    """
    # The first task gets the list of URLs.
    # The second task (process_url_list) receives this list and creates the parallel jobs.
    workflow = chain(
        scrape_links.s(),
        process_url_list.s()
    )
    workflow.delay()
    print("Scraping workflow initiated.")

@shared_task
def process_url_list(urls):
    """
    Receives a list of URLs and creates a group of parallel processing chains.
    Each chain validates one URL and then generates a PDF for it.
    """
    if not urls:
        print("No URLs to process.")
        return

    print(f"Dispatching {len(urls)} parallel jobs...")

    # Create a group of chains.
    # Each element in the group is a mini-workflow for one URL.
    job_group = group(
        chain(
            filter_scraped_urls.s(url)    # Step 1: Filter this specific URL
            #, some_stage.s()          # Step 2: Submit to next stage of pipeline if passed
        ) for url in urls
    )

    # Run the entire group of jobs in parallel
    job_group.delay()
    
    print(f"Group of {len(urls)} jobs has been dispatched to workers.")