from celery import shared_task

@shared_task
def generate_pdf_task(url):
    print(f"Simulating download of: {url}")
