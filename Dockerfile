FROM python:3.12-slim

WORKDIR /app

COPY application/ ./application
COPY wsgi.py ./wsgi.py
COPY requirements.txt ./requirements.txt

RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]
