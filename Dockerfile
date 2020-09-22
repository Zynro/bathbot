FROM python:3.7

RUN apt-get update && \
    apt-get upgrade -y \
    apt-get install -y git

ADD botr.py /

COPY requirements.txt /tmp
WORKDIR /tmp
RUN pip install -r requirements.txt

CMD ["python", "./botr.py"]