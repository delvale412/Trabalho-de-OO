FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

RUN python setup_db.py

EXPOSE 8080

CMD ["python", "app.py"]