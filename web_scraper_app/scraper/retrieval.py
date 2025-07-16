from bs4 import BeautifulSoup
from celery import shared_task
import asyncio
from pyppeteer import launch
import requests

@shared_task
async def generate_pdf_task(url):
    response = requests.get(url).text

    soup = BeautifulSoup(response, 'html.parser')

    title = url
    for tag in [soup.find('title'), soup.find('h1'), soup.find('h2'), soup.find('h3')]:
        if tag and tag.get_text(strip=True):
            title = tag.get_text(strip=True)
            break


    browser = await launch()
    page = await browser.newPage()
    
    await page.goto(url)
    
    pdf_path = f"./gdrive/saved_sites/{title}.pdf" 
    
    await page.pdf({'path': pdf_path, 'format': 'A4'})
    
    await browser.close()

    print(f"Simulating download of: {url}")

    return pdf_path


#def main():
    #asyncio.get_event_loop().run_until_complete(generate_pdf_task('https://apitemplate.io/blog/how-to-convert-html-to-pdf-using-python/'))

#main()
"""
import asyncio
from pyppeteer import launch

async def generate_pdf(url, pdf_path):
    browser = await launch()
    page = await browser.newPage()
    
    await page.goto(url)
    
    await page.pdf({'path': pdf_path, 'format': 'A4'})
    
    await browser.close()


def main():
    asyncio.get_event_loop().run_until_complete(generate_pdf('https://apitemplate.io/blog/how-to-convert-html-to-pdf-using-python/', 'example.pdf'))

main() 


"""