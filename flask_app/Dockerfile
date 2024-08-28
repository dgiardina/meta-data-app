# FROM python:3.6.7
FROM python:3.11
ENV TZ="Africa/Lusaka"
WORKDIR usr/src/flask_app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
