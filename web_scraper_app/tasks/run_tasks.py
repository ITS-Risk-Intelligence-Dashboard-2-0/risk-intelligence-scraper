from ..celery import app
from ..crawler.tasks import scrape_google_links
from ..scraper.tasks import generate_pdf_task
import time

if __name__ == '__main__':
    print("Scraping Google links...")
    urls = scrape_google_links()

    print(f"Found {len(urls)} URLs. Dispatching tasks...")

    tasks_to_monitor = []
    task_start_times = {}
    for idx, url in enumerate(urls):
        result = generate_pdf_task.delay(url)
        print(f"Task 'generate_pdf_task({url})' dispatched with ID: {result.id}")
        tasks_to_monitor.append((f"generate_pdf_task({url})", result))
        task_start_times[result.id] = time.monotonic()

    print(f"\nWaiting for {len(tasks_to_monitor)} tasks to complete...")

    while tasks_to_monitor:
        # Iterate over a copy of the list to allow safe removal
        for task_name, task_obj in tasks_to_monitor[:]:
            if task_obj.ready():
                end_time = time.monotonic()
                start_time = task_start_times.get(task_obj.id, end_time)
                duration = end_time - start_time

                print(f"\nTask '{task_name}' (ID: {task_obj.id}) finished in {duration:.2f} seconds.")
                try:
                    value = task_obj.get()
                    print(f"Result: {value}")
                except Exception as e:
                    print(f"Task execution resulted in an error: {e}")

                print(f"Task state: {task_obj.state}")
                
                # Remove the completed task from the monitoring list
                tasks_to_monitor.remove((task_name, task_obj))

        time.sleep(0.5)

    print("\nAll tasks have completed.")

