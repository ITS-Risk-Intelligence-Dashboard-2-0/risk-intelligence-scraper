from celery import shared_task
from playwright.sync_api import sync_playwright
import requests
import uuid

from gdrive.api import GoogleDriveService
from shared.core_lib.db_utils import establish_connection, insert_articles

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

        gdrive = GoogleDriveService()
        conn, cur = establish_connection()

        for url, category, _ in pages_batch:
            category_name, category_folder = category
            hyphened_category_name = category_name.replace(" ", "-")

            file_id = uuid.uuid4()
            install_filename = str(file_id).replace("-", "_")

            install_page_as_pdf(page, url, f"/app/pages/{hyphened_category_name}-{install_filename}.pdf", 5000, 2)

            drive_file_id = gdrive.upload_file(category_folder, f"{install_filename}.pdf", f"/app/pages/{hyphened_category_name}-{install_filename}.pdf")

            insert_articles(conn, cur, file_id, drive_file_id, url)

            print(f"INSTALLED {url} => {install_filename}.pdf")

        cur.close()
        conn.close()

        page.close()
        browser.close()

    return len(pages_batch)

@shared_task
def retrieve_pdf(pages):
    if len(pages) == 0:
        return
    print("FETCHING")
    url, category, content = pages[0]
    category_name, category_folder = category

    response = requests.get(url)
    status = response.status_code
    if status // 100 != 2:
        print(f"ERROR retrieving pdf from {url}")
        return None

    file_id = uuid.uuid4()
    install_filename = str(file_id).replace("-", "_")
    hyphened_category_name = category_name.replace(" ", "-")

    with open(f"/app/pages/{hyphened_category_name}-{install_filename}.pdf", "wb") as f:
        f.write(response.content)

    gdrive = GoogleDriveService()
    drive_file_id = gdrive.upload_file(category_folder, f"{install_filename}.pdf", f"/app/pages/{hyphened_category_name}-{install_filename}.pdf")

    conn, cur = establish_connection()
    insert_articles(conn, cur, file_id, drive_file_id, url)
    cur.close()
    conn.close()

    print("PDF successfully written")
