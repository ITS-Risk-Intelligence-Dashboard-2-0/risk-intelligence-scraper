from celery import shared_task
from playwright.sync_api import sync_playwright
import requests
import uuid

def install_page_as_pdf(page, url, path, timeout_time, max_retry):
    for _ in range(max_retry):
        try:
            page.goto(url, wait_until="networkidle")
            page.pdf(path=path)

            return True
        except TimeoutError:
            continue
        except Exception:
            return False

    try:
        page.goto(url, wait_until="load")
        page.pdf(path=path)

        return True
    except:
        return False

@shared_task
def retrieve_page(url_batch, browser):
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(browser)
        page = browser.new_page()

        for url in url_batch:
            install_filename = str(uuid.uuid4()).replace("-", "_")

            install_page_as_pdf(page, url, f"/app/pages/{install_filename}.pdf", 5000, 2)

            print(f"INSTALLED {url} => {install_filename}.pdf")

        page.close()
        browser.close()

@shared_task
def retrieve_pdf(urls):
    response = requests.get(urls[0])
    status = response.status_code
    if status // 100 != 2:
        print(f"ERROR retrieving pdf from {urls[0]}")
        return None

    install_filename = str(uuid.uuid4()).replace("-", "_")
    with open(f"/app/pages/fff{install_filename}.pdf", "wb") as f:
        f.write(response.content)

    print("PDF successfully written")
