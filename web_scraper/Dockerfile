FROM python:3.10-slim
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /app
COPY requirements.txt .
RUN pip install pdfplumber
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install playwright
RUN python -m playwright install
RUN python -m playwright install-deps
RUN pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
COPY . .