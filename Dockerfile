FROM python:3-alpine

EXPOSE 5000

WORKDIR /app

RUN apk add --no-cache \
		python3-dev \
		build-base \
		linux-headers
		
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

CMD [ "uwsgi", "--ini", "/app/wsgi.ini" ]