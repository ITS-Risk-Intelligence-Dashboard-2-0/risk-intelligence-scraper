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
