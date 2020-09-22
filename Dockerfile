FROM python:3.7

ADD botr.py /

COPY requirements.txt /tmp
WORKDIR /tmp
RUN pip install -r requirements.txt

CMD ["python", "./botr.py"]