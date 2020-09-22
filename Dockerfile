FROM python:3.7

RUN apt-get update && apt-get install -y git

COPY requirements.txt /tmp
WORKDIR /tmp

COPY . /app/bathbot
WORKDIR /app/bathbot
ENV PYTHONPATH /app/bathbot

CMD ["python", "./botr.py"]