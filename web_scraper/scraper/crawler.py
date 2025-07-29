from celery import shared_task
from urllib.parse import urlparse, urlunparse

from playwright.sync_api import sync_playwright

def build_url(current_url, scraped_url):
    return urlunparse(("https", current_url.netloc, scraped_url.path, '', '', ''))

def same_domain(netloc1, netloc2):
    if netloc1 == '' or netloc2 == '':
        return True

    domain_levels1 = netloc1.split('.')
    domain_levels2 = netloc2.split('.')

    try:
        same_top_domain = domain_levels1[-1] == domain_levels2[-1]
        same_second_domain = domain_levels1[-2] == domain_levels2[-2]
    except:
        return False

    return same_top_domain and same_second_domain

def analyze_last_path(chunk):
    words = chunk.split("-")
    if len(words) < 3:
        return False

    for word in words:
        for c in word:
            if c >= 'a' and c <= 'z':
                continue

            if c >= 'A' and c <= 'Z':
                continue

            if c >= '0' and c <= '9':
                continue

            if c == '-' or c == '.':
                continue

            return False

    return True

def probably_news(path):
    path_chunks = path.rstrip("/").split("/")
    is_article = analyze_last_path(path_chunks[-1])

    if not is_article:
        return None

    return "/".join(path_chunks[:-1])

def is_pdf(path):
    trimmed = path.rstrip("/")
    return trimmed.endswith(".pdf")

def playwright_retrieve_urls(page, url, timeout_time, max_retry):
    for _ in range(max_retry):
        try:
            page.goto(url, wait_until="networkidle", timeout=timeout_time)
            urls = page.eval_on_selector_all(
                "a",
                "elems => elems.map(elem => elem.href)"
            )

            return urls

        except TimeoutError:
            continue
        except Exception as e:
            print(e)
            return []

@shared_task
def scrape_links(browser, sources_data, crawl_depth):
    # Convert the source data from the API into the format the crawler expects
    source_hubs = [{"url": s['url'], "depth": crawl_depth, "target_type": s['target_type']} for s in sources_data]
    
    processed_urls = set()

    found_urls = set()
    found_pdfs = set()

    with sync_playwright() as p:
        # initialize browser and page for crawling
        browser = p.chromium.connect_over_cdp(browser)
        page = browser.new_page()

        while len(source_hubs) > 0:
            # grab an item from the queue
            curr_item = source_hubs.pop()
            curr_source = curr_item["url"]
            if curr_item["depth"] > crawl_depth:
                continue
            if curr_source in processed_urls:
                continue
            
            processed_urls.add(curr_source)

            curr_source_parsed = urlparse(curr_source)

            urls = playwright_retrieve_urls(page, curr_source, 60000, 3)

            # analyze the urls
            for url in urls:
                scraped_url_parsed = urlparse(url)

                if not same_domain(scraped_url_parsed.netloc, curr_source_parsed.netloc):
                    continue

                built_url = build_url(curr_source_parsed, scraped_url_parsed)

                # Respect the target_type for the source
                target_type = curr_item.get("target_type", "BOTH")
                is_pdf_target = is_pdf(scraped_url_parsed.path)

                if is_pdf_target and target_type in ["PDF", "BOTH"]:
                    if built_url not in found_pdfs:
                        found_pdfs.add(built_url)
                        continue
                
                if not is_pdf_target and target_type in ["WEBSITE", "BOTH"]:
                    source_hubs.append({
                        "url": built_url,
                        "depth": curr_item["depth"] + 1,
                        "target_type": target_type
                    })

                    if probably_news(scraped_url_parsed.path):
                        if built_url not in found_urls:
                            found_urls.add(built_url)

        page.close()
        browser.close()

    print(f"Scraping complete! Found {len(found_urls)} potential news URLs and {len(found_pdfs)} pdfs!")
    return (list(found_urls), list(found_pdfs))
