FROM python:3.10-slim

WORKDIR /usr/src/flask_app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . .

ENV FLASK_APP=weather.py
ENV FLASK_RUN_HOST=0.0.0.0

EXPOSE 5000

CMD ["flask", "run"]
