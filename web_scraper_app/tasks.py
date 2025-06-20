import time
from .celery import app

@app.task
def add(x, y):
    """A simple task that adds two numbers."""
    time.sleep(5) # Simulate some work
    return x + y

@app.task
def add_long(x, y):
    """A simple task that adds two numbers."""
    time.sleep(10) # Simulate some work
    return x + y

@app.task(bind=True, max_retries=3)
def long_running_task(self, duration):
    """A task that simulates a long process and can be retried."""
    try:
        print(f"Task starting for {duration} seconds...")
        # Your complex logic here
        if duration < 0:
            raise ValueError("Duration cannot be negative.")
        time.sleep(duration)
        print("Task completed successfully.")
        return {"status": "Completed", "duration": duration}
    except Exception as exc:
        print(f"Task failed. Retrying in 5 seconds... (Attempt {self.request.retries + 1})")
        # Retry the task after 5 seconds
        raise self.retry(exc=exc, countdown=5)