import requests
from bs4 import BeautifulSoup

def main():
    url = "https://www.google.com/"
    data = requests.get(url)

    soup = BeautifulSoup(data.text, "html.parser")

    links = soup.find_all("a")

    for link in links:
        print(link.href)

main()
