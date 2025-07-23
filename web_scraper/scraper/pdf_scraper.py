import urllib3
import pdfplumber
from io import BytesIO

from celery import shared_task

@shared_task
def scrape_pdf_text(url):
    all_text = ""
    http = urllib3.PoolManager()
    temp = BytesIO()
    temp.write(http.request("GET", url).data)

    try:    # to verify is the url has valid pdf file!
        pdf = pdfplumber.open(temp)
        for pdf_page in pdf.pages:
            single_page_text = pdf_page.extract_text()
            # TypeError: can only concatenate str (not "NoneType") to str
            if single_page_text is not None: 
                all_text += '\n' + single_page_text
        pdf.close()
    except:
        pass

    return ([url], [all_text])
