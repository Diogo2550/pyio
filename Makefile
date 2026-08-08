IMAGE           := pyio
DOCKERHUB_IMAGE := diogo2550/pyio
TAG             := latest
PORT            := 5001
WORKERS         := 2

.PHONY: build dev stop logs docker-build docker-push

build:
	docker build -t $(IMAGE) .

dev: build
	docker run --rm --name $(IMAGE) -p $(PORT):5000 -v $(CURDIR)/:/app $(IMAGE) \
		uwsgi --ini /app/uwsgi.ini --py-autoreload=1 --touch-reload=app.py --processes $(WORKERS)

stop:
	docker stop $(IMAGE)

logs:
	docker logs -f $(IMAGE)

docker-build:
	docker build -t $(DOCKERHUB_IMAGE):$(TAG) .

docker-push: docker-build
	docker push $(DOCKERHUB_IMAGE):$(TAG)
