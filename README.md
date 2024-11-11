## Instalar projeto

docker build -t thumb .

## Executar Produção

docker run --name thumb -p 5000:5000 thumb

## Executar Desenvolvimento

docker run --name thumb -p 5000:5000 -v `pwd`/:/app thumb uwsgi --ini /app/uwsgi.ini --py-autoreload=1 --touch-reload=app.py

# Deploy

Olhar o arquivo uwsgi.ini e alterar os valores necessários, principalmente o:

- processes
- socket
- http