from celery import shared_task

from playwright.sync_api import sync_playwright

def playwright_retrieve_paragraphs(page, url, timeout_time, max_retry):
    for _ in range(max_retry):
        try:
            page.goto(url, wait_until="networkidle", timeout=timeout_time)
            p_tags = page.eval_on_selector_all("p", "elements => elements.map(el => el.innerText)")
            texts = [p.strip() for p in p_tags]
            texts = list(filter(lambda p: len(p.split()) > 3, texts))

            return " ".join(texts)

        except TimeoutError:
            continue
        except Exception as e:
            print(e)
            return ""

@shared_task
def filter_scraped_urls(batch):
    url_batch, browser_connection = batch
    urls = []
    page_contents = []

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(browser_connection)
        page = browser.new_page()

        for url in url_batch:
            page_content = playwright_retrieve_paragraphs(page, url, 10000, 3)

            if len(page_content.split()) > 200:
                urls.append(url)
                page_contents.append(page_content)

        page.close()
        browser.close()

    return (urls, page_contents)
