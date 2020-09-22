FROM python:3.8

ADD botr.py

RUN pip install pip install -r requirements.txt