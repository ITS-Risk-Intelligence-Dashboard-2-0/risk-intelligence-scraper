from celery import shared_task
from playwright.sync_api import sync_playwright
import requests
import uuid

from gdrive.api import authenticate_drive, upload_pdf_to_drive

def install_page_as_pdf(page, url, path, timeout_time, max_retry):
    for _ in range(max_retry):
        try:
            page.goto(url, wait_until="networkidle")
            page.pdf(path=path)

            return True
        except TimeoutError:
            continue
        except Exception as e:
            print(f"{e} RETRYING ...")
            continue

    try:
        page.goto(url, wait_until="load")
        page.pdf(path=path)

        return True
    except:
        print(f"{e}")
        return False

@shared_task
def retrieve_page(pages_batch, browser):
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(browser)
        page = browser.new_page()

        for url, category, _ in pages_batch:
            install_filename = str(uuid.uuid4()).replace("-", "_")
            install_filename = f"{category.replace(' ', '')}--{install_filename}"

            install_page_as_pdf(page, url, f"/app/pages/{install_filename}.pdf", 5000, 2)

            print(f"INSTALLED {url} => {install_filename}.pdf")

        page.close()
        browser.close()

    return len(pages_batch)

@shared_task
def retrieve_pdf(pages):
    if len(pages) == 0:
        return
    print("FETCHING")
    url, category, content = pages[0]

    response = requests.get(url)
    status = response.status_code
    if status // 100 != 2:
        print(f"ERROR retrieving pdf from {url}")
        return None

    install_filename = str(uuid.uuid4()).replace("-", "_")
    install_filename = f"{category.replace(' ', '')}--{install_filename}"

    with open(f"/app/pages/pdf-{install_filename}.pdf", "wb") as f:
        f.write(response.content)

    with open(f"/app/pages/pdf-{install_filename}.txt", "w") as f:
        f.write(content)

    #google_drive_auth = authenticate_drive()
    #upload_pdf_to_drive(google_drive_auth, f"/app/pages/{install_filename}.pdf", "1Qh4SXXuCeN_21-D-XHWRKp8KecAQYbjx")
    print("PDF successfully written")
