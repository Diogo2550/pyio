FROM python:3.9-alpine

EXPOSE 5000

WORKDIR /app

RUN apk update && apk upgrade --no-cache

RUN apk add --no-cache \
		python3-dev \
		build-base \
		linux-headers \
        ffmpeg
		
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

CMD [ "uwsgi", "--ini", "/app/uwsgi.ini" ]