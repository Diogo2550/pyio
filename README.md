## Instalar projeto

docker build -t thumb .

## Executar Produção

docker run --name thumb -p 5000:5000 --restart unless-stopped -d thumb

## Executar Desenvolvimento

docker run --name thumb -p 5000:5000 -v `pwd`/:/app thumb uwsgi --ini /app/uwsgi.ini --py-autoreload=1 --touch-reload=app.py

# Deploy

Olhar o arquivo uwsgi.ini e alterar os valores necessários, principalmente o:

- processes
- socket
- http

# API Reference

Em modo local:
Enviar uma requisição para {schema}://{host}/{path/file.mp4}/{param1:value/param2:value...}/thumb para gerar uma thumb do vídeo, onde:

Params:
[Size] s: {width}|{width}x{height} -> width|height sendo inteiros
[Quality] q:{quality} -> 1 < quality <= 100
[Proportion] p: -> sua existência habilita a necessidade de mantera a proporção da imagem