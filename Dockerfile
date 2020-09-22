FROM python:3.7

RUN apt-get update && apt-get install -y git

COPY . /app/bathbot
WORKDIR /app/bathbot
RUN pip install -r requirements.txt
ENV PYTHONPATH /app/bathbot

CMD ["python", "./botr.py"]