FROM python:3.6.8-stretch
WORKDIR /srv/app/

COPY ./requirements.txt .
RUN pip install -r requirements.txt

RUN apt-get update && \
	apt-get install -y ffmpeg

ENV BATH_ENV='local'

COPY . .

CMD ["./runserver.sh"]
