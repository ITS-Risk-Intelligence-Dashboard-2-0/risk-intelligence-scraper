import requests
from bs4 import BeautifulSoup

def main():
    open_set = set(["https://en.wikipedia.org/wiki/Main_Page"])
    close_set = set()

    while open_set:
        curr_url = open_set.pop()
        close_set.add(curr_url)

        request_info = requests.get(curr_url)

        soup = BeautifulSoup(request_info.text, "html.parser")

        links = soup.find_all("a")

        for link in links:
            url = link.get("href")
            if url in open_set:
                continue
            if url in close_set:
                continue

            if url and url.startswith("http"):
                open_set.add(url)
                print(url)

main()
